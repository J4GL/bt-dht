"""
DHT Client implementation for BitTorrent DHT network.

This module implements a working DHT client that can:
- Bootstrap from known DHT nodes
- Perform iterative lookups for nodes and peers
- Send and receive DHT queries/responses over UDP
- Maintain a routing table of known nodes

Reference: BEP 5 - DHT Protocol
https://www.bittorrent.org/beps/bep_0005.html
"""

import socket
import threading
import time
import random
from typing import Dict, List, Set, Tuple, Optional, Callable
from collections import defaultdict

from node import Node, generate_node_id, distance
from routing_table import RoutingTable
from protocol import (
    create_ping_query,
    create_find_node_query,
    create_get_peers_query,
    parse_message,
    unpack_nodes
)


class DHTClient:
    """
    BitTorrent DHT client for peer discovery.

    This client implements the Kademlia-based DHT protocol used by BitTorrent
    for decentralized peer discovery without relying on centralized trackers.

    Attributes:
        node_id (bytes): This client's 20-byte node ID
        port (int): UDP port to listen on
        routing_table (RoutingTable): K-bucket routing table
        socket (socket.socket): UDP socket for communication
        running (bool): Whether the client is running
    """

    # Default bootstrap nodes (BitTorrent mainline DHT)
    DEFAULT_BOOTSTRAP_NODES = [
        ('router.bittorrent.com', 6881),
        ('dht.transmissionbt.com', 6881),
        ('router.utorrent.com', 6881),
    ]

    def __init__(self, port: int = 0, node_id: bytes = None):
        """
        Initialize DHT client.

        Args:
            port: UDP port to bind to (0 = random port)
            node_id: 20-byte node ID (None = generate random)

        Raises:
            ValueError: If port is invalid
            TypeError: If node_id has wrong type
        """
        # Validate port
        if not isinstance(port, int):
            raise TypeError("port must be int")
        if port < 0 or port > 65535:
            raise ValueError(f"port must be 0-65535, got {port}")

        # Generate or validate node ID
        if node_id is None:
            self.node_id = generate_node_id()
        else:
            if not isinstance(node_id, bytes) or len(node_id) != 20:
                raise ValueError("node_id must be 20 bytes")
            self.node_id = node_id

        self.port = port
        self.routing_table = RoutingTable(self.node_id, k=8)

        # Communication
        self.socket = None
        self.running = False
        self.receive_thread = None

        # Pending queries: transaction_id -> (query_type, callback, timestamp)
        self.pending_queries: Dict[bytes, Tuple[str, Callable, float]] = {}
        self.pending_lock = threading.Lock()

        # Transaction ID counter
        self.transaction_counter = 0

        # Timeout for queries
        self.query_timeout = 5.0  # seconds

        # Discovered info_hashes (for crawler mode)
        self.discovered_info_hashes: Dict[bytes, Dict] = {}
        self.info_hash_callback: Optional[Callable] = None

    def start(self):
        """
        Start the DHT client.

        Creates UDP socket, binds to port, and starts receive thread.

        Raises:
            RuntimeError: If client is already running
            OSError: If socket cannot be created or bound
        """
        if self.running:
            raise RuntimeError("DHT client already running")

        # Create UDP socket
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        # Bind to port
        self.socket.bind(('0.0.0.0', self.port))

        # Get actual port if random was requested
        if self.port == 0:
            self.port = self.socket.getsockname()[1]

        self.running = True

        # Start receive thread
        self.receive_thread = threading.Thread(target=self._receive_loop, daemon=True)
        self.receive_thread.start()

        print(f"[DHT] Started on port {self.port}, Node ID: {self.node_id.hex()[:16]}...")

    def stop(self):
        """Stop the DHT client."""
        if not self.running:
            return

        self.running = False

        if self.socket:
            self.socket.close()

        if self.receive_thread:
            self.receive_thread.join(timeout=2.0)

        print("[DHT] Stopped")

    def bootstrap(self, bootstrap_nodes: List[Tuple[str, int]] = None):
        """
        Bootstrap the DHT by connecting to known nodes.

        Args:
            bootstrap_nodes: List of (host, port) tuples (None = use defaults)

        Returns:
            bool: True if bootstrap was successful
        """
        if not self.running:
            raise RuntimeError("DHT client not running")

        if bootstrap_nodes is None:
            bootstrap_nodes = self.DEFAULT_BOOTSTRAP_NODES

        print(f"[DHT] Bootstrapping from {len(bootstrap_nodes)} nodes...")

        success_count = 0

        for host, port in bootstrap_nodes:
            try:
                # Resolve hostname
                ip = socket.gethostbyname(host)

                # Send find_node query for our own ID
                # This populates our routing table with nodes
                def bootstrap_callback(response, addr):
                    nonlocal success_count
                    if b'r' in response and b'nodes' in response[b'r']:
                        nodes_data = response[b'r'][b'nodes']
                        nodes = unpack_nodes(nodes_data)
                        for node_id, node_ip, node_port in nodes:
                            node = Node(node_id, node_ip, node_port)
                            self.routing_table.add_node(node)
                        success_count += 1
                        print(f"[DHT] Bootstrap: received {len(nodes)} nodes from {addr[0]}")

                self._send_find_node(ip, port, self.node_id, bootstrap_callback)

            except (socket.gaierror, OSError) as e:
                print(f"[DHT] Bootstrap failed for {host}:{port} - {e}")

        # Wait a bit for responses
        time.sleep(2.0)

        # Clean up timed out queries
        self._cleanup_pending()

        print(f"[DHT] Bootstrap complete: {success_count}/{len(bootstrap_nodes)} nodes responded")

        return success_count > 0

    def find_node(self, target_id: bytes, count: int = 8) -> List[Node]:
        """
        Find nodes closest to a target ID using iterative lookup.

        Args:
            target_id: 20-byte target node ID
            count: Number of closest nodes to find

        Returns:
            List of closest nodes found

        Raises:
            ValueError: If target_id is invalid
        """
        if not isinstance(target_id, bytes) or len(target_id) != 20:
            raise ValueError("target_id must be 20 bytes")

        print(f"[DHT] Finding nodes close to {target_id.hex()[:16]}...")

        # Get initial closest nodes from routing table
        closest = self.routing_table.get_closest_nodes(target_id, count=count * 2)

        if not closest:
            print("[DHT] No nodes in routing table, bootstrap first")
            return []

        # Track queried nodes
        queried: Set[bytes] = set()
        found_nodes: Dict[bytes, Node] = {node.node_id: node for node in closest}

        # Iterative lookup
        for _ in range(3):  # Limit iterations
            # Get unqueried closest nodes
            to_query = [
                node for node in sorted(
                    found_nodes.values(),
                    key=lambda n: distance(n.node_id, target_id)
                )[:count]
                if node.node_id not in queried
            ]

            if not to_query:
                break

            # Query nodes
            for node in to_query[:3]:  # Query 3 at a time
                queried.add(node.node_id)

                def find_callback(response, addr):
                    if b'r' in response and b'nodes' in response[b'r']:
                        nodes_data = response[b'r'][b'nodes']
                        nodes = unpack_nodes(nodes_data)
                        for node_id, node_ip, node_port in nodes:
                            if node_id not in found_nodes:
                                found_nodes[node_id] = Node(node_id, node_ip, node_port)
                                self.routing_table.add_node(found_nodes[node_id])

                self._send_find_node(node.ip, node.port, target_id, find_callback)

            time.sleep(0.5)  # Brief wait for responses

        # Return closest nodes
        result = sorted(
            found_nodes.values(),
            key=lambda n: distance(n.node_id, target_id)
        )[:count]

        print(f"[DHT] Found {len(result)} nodes")
        return result

    def get_peers(self, info_hash: bytes, timeout: float = 10.0) -> List[Tuple[str, int]]:
        """
        Find peers for a torrent with given info_hash.

        Args:
            info_hash: 20-byte torrent info hash
            timeout: Maximum time to search (seconds)

        Returns:
            List of (ip, port) tuples for peers

        Raises:
            ValueError: If info_hash is invalid
        """
        if not isinstance(info_hash, bytes) or len(info_hash) != 20:
            raise ValueError("info_hash must be 20 bytes")

        print(f"[DHT] Searching for peers for info_hash {info_hash.hex()[:16]}...")

        peers: Set[Tuple[str, int]] = set()
        start_time = time.time()

        # Get initial closest nodes
        closest = self.routing_table.get_closest_nodes(info_hash, count=16)

        if not closest:
            print("[DHT] No nodes in routing table")
            return []

        queried: Set[bytes] = set()
        to_query = list(closest)

        while to_query and (time.time() - start_time) < timeout:
            # Get next nodes to query
            batch = to_query[:5]
            to_query = to_query[5:]

            for node in batch:
                if node.node_id in queried:
                    continue

                queried.add(node.node_id)

                def peer_callback(response, addr):
                    if b'r' not in response:
                        return

                    r = response[b'r']

                    # Check for peers (6-byte compact format: 4 IP + 2 port)
                    if b'values' in r:
                        values = r[b'values']
                        if isinstance(values, list):
                            for peer_data in values:
                                if len(peer_data) == 6:
                                    ip_bytes = peer_data[:4]
                                    port_bytes = peer_data[4:6]
                                    ip = socket.inet_ntoa(ip_bytes)
                                    port = int.from_bytes(port_bytes, 'big')
                                    peers.add((ip, port))

                    # Check for closer nodes
                    if b'nodes' in r:
                        nodes_data = r[b'nodes']
                        try:
                            nodes = unpack_nodes(nodes_data)
                            for node_id, node_ip, node_port in nodes:
                                new_node = Node(node_id, node_ip, node_port)
                                if node_id not in queried:
                                    to_query.append(new_node)
                                    self.routing_table.add_node(new_node)
                        except ValueError:
                            pass

                self._send_get_peers(node.ip, node.port, info_hash, peer_callback)

            time.sleep(0.3)  # Small delay between batches
            self._cleanup_pending()

        print(f"[DHT] Found {len(peers)} peers")
        return list(peers)

    def _send_find_node(self, ip: str, port: int, target_id: bytes, callback: Callable):
        """Send find_node query."""
        transaction_id = self._get_transaction_id()
        query = create_find_node_query(transaction_id, self.node_id, target_id)

        with self.pending_lock:
            self.pending_queries[transaction_id] = ('find_node', callback, time.time())

        self.socket.sendto(query, (ip, port))

    def _send_get_peers(self, ip: str, port: int, info_hash: bytes, callback: Callable):
        """Send get_peers query."""
        transaction_id = self._get_transaction_id()
        query = create_get_peers_query(transaction_id, self.node_id, info_hash)

        with self.pending_lock:
            self.pending_queries[transaction_id] = ('get_peers', callback, time.time())

        self.socket.sendto(query, (ip, port))

    def _get_transaction_id(self) -> bytes:
        """Generate unique transaction ID."""
        self.transaction_counter += 1
        return self.transaction_counter.to_bytes(2, 'big')

    def _receive_loop(self):
        """Main receive loop (runs in thread)."""
        self.socket.settimeout(1.0)

        while self.running:
            try:
                data, addr = self.socket.recvfrom(2048)
                threading.Thread(
                    target=self._handle_message,
                    args=(data, addr),
                    daemon=True
                ).start()
            except socket.timeout:
                continue
            except OSError:
                if self.running:
                    print(f"[DHT] Socket error in receive loop")
                break

    def _handle_message(self, data: bytes, addr: Tuple[str, int]):
        """Handle incoming DHT message."""
        try:
            message = parse_message(data)

            # Handle responses
            if message[b'y'] == b'r':
                transaction_id = message[b't']

                with self.pending_lock:
                    if transaction_id in self.pending_queries:
                        query_type, callback, timestamp = self.pending_queries.pop(transaction_id)
                        callback(message, addr)

            # Handle incoming queries (for crawler mode)
            elif message[b'y'] == b'q':
                self._handle_query(message, addr)

        except (ValueError, KeyError) as e:
            # Ignore malformed messages
            pass

    def _handle_query(self, message: Dict, addr: Tuple[str, int]):
        """Handle incoming DHT query."""
        try:
            query_type = message.get(b'q')
            args = message.get(b'a', {})
            transaction_id = message.get(b't', b'')

            # Extract info_hash from get_peers queries (crawler mode)
            if query_type == b'get_peers' and b'info_hash' in args:
                info_hash = args[b'info_hash']
                if len(info_hash) == 20:
                    # New info_hash discovered!
                    if info_hash not in self.discovered_info_hashes:
                        self.discovered_info_hashes[info_hash] = {
                            'first_seen': time.time(),
                            'peer_count': 1,
                            'sources': [addr[0]]
                        }

                        # Call callback if registered
                        if self.info_hash_callback:
                            self.info_hash_callback(info_hash, addr)
                    else:
                        self.discovered_info_hashes[info_hash]['peer_count'] += 1
                        if addr[0] not in self.discovered_info_hashes[info_hash]['sources']:
                            self.discovered_info_hashes[info_hash]['sources'].append(addr[0])

                    # Send response (pretend we don't have peers)
                    self._send_get_peers_response(transaction_id, addr)

            # Respond to ping
            elif query_type == b'ping':
                self._send_ping_response(transaction_id, addr)

            # Respond to find_node
            elif query_type == b'find_node' and b'target' in args:
                self._send_find_node_response(transaction_id, args[b'target'], addr)

        except (ValueError, KeyError):
            pass

    def _send_ping_response(self, transaction_id: bytes, addr: Tuple[str, int]):
        """Send ping response."""
        from bencode import encode
        response = {
            b't': transaction_id,
            b'y': b'r',
            b'r': {b'id': self.node_id}
        }
        try:
            self.socket.sendto(encode(response), addr)
        except:
            pass

    def _send_find_node_response(self, transaction_id: bytes, target: bytes, addr: Tuple[str, int]):
        """Send find_node response with closest nodes."""
        from bencode import encode
        from protocol import pack_nodes

        # Get closest nodes from routing table
        closest = self.routing_table.get_closest_nodes(target, count=8)
        nodes_data = pack_nodes([(n.node_id, n.ip, n.port) for n in closest]) if closest else b''

        response = {
            b't': transaction_id,
            b'y': b'r',
            b'r': {
                b'id': self.node_id,
                b'nodes': nodes_data
            }
        }
        try:
            self.socket.sendto(encode(response), addr)
        except:
            pass

    def _send_get_peers_response(self, transaction_id: bytes, addr: Tuple[str, int]):
        """Send get_peers response (with nodes, not peers)."""
        from bencode import encode
        from protocol import pack_nodes

        # We don't have peers, send nodes instead
        closest = list(self.routing_table.get_closest_nodes(self.node_id, count=8))
        nodes_data = pack_nodes([(n.node_id, n.ip, n.port) for n in closest]) if closest else b''

        response = {
            b't': transaction_id,
            b'y': b'r',
            b'r': {
                b'id': self.node_id,
                b'token': b'aoeusnth',  # Dummy token
                b'nodes': nodes_data
            }
        }
        try:
            self.socket.sendto(encode(response), addr)
        except:
            pass

    def crawl_network(self, duration: float = 60.0, callback: Callable = None):
        """
        Crawl the DHT network to discover info_hashes.

        This method makes the client join the DHT and respond to queries,
        allowing it to observe what info_hashes are being searched for.

        Args:
            duration: How long to crawl (seconds, 0 = infinite)
            callback: Optional callback(info_hash, addr) for each discovery

        Returns:
            Dict mapping info_hash to metadata
        """
        if not self.running:
            raise RuntimeError("DHT client not running")

        print(f"[DHT] Starting crawler mode (duration: {duration}s)...")

        self.info_hash_callback = callback
        start_time = time.time()

        # Continuously query random node IDs to maintain presence in DHT
        query_count = 0
        while (duration == 0 or (time.time() - start_time) < duration):
            try:
                # Query random nodes to stay active in DHT
                if query_count % 10 == 0:  # Every 10 iterations
                    # Get some nodes from routing table
                    all_nodes = []
                    for bucket in self.routing_table.buckets:
                        all_nodes.extend(bucket)

                    if all_nodes:
                        # Pick random nodes to query
                        nodes_to_query = random.sample(all_nodes, min(5, len(all_nodes)))
                        for node in nodes_to_query:
                            # Query for random target to maintain routing table
                            random_target = generate_node_id()

                            def dummy_callback(response, addr):
                                pass  # We just want to stay active

                            self._send_find_node(node.ip, node.port, random_target, dummy_callback)

                query_count += 1
                time.sleep(1.0)  # Check every second

                # Clean up old queries
                if query_count % 30 == 0:
                    self._cleanup_pending()

            except KeyboardInterrupt:
                break

        self.info_hash_callback = None
        return dict(self.discovered_info_hashes)

    def _cleanup_pending(self):
        """Remove timed out pending queries."""
        now = time.time()
        with self.pending_lock:
            to_remove = [
                tid for tid, (_, _, timestamp) in self.pending_queries.items()
                if now - timestamp > self.query_timeout
            ]
            for tid in to_remove:
                del self.pending_queries[tid]
