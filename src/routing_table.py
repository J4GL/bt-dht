"""
Kademlia Routing Table implementation.

This module implements the routing table (K-buckets) used in the Kademlia DHT protocol.
The routing table organizes known nodes into buckets based on their XOR distance from
the local node, allowing efficient routing of queries across the network.

Key concepts:
- K-buckets: Lists of nodes at specific distance ranges
- K value: Maximum nodes per bucket (typically 8 or 20)
- 160 buckets: One for each bit position in the 160-bit node ID space
- LRU eviction: Least Recently Used nodes are replaced when buckets are full

Reference: BEP 5 - DHT Protocol
https://www.bittorrent.org/beps/bep_0005.html

Kademlia Paper:
Maymounkov, P., & Mazières, D. (2002). Kademlia: A peer-to-peer information system
based on the XOR metric.
"""

from typing import List, Optional
from node import Node, distance


class RoutingTable:
    """
    Kademlia routing table for managing known DHT nodes.

    The routing table consists of 160 K-buckets (one for each bit in the 160-bit ID space).
    Each bucket contains up to K nodes that share a specific distance range from the local node.

    Bucket i contains nodes where the XOR distance has the i-th bit as the most significant
    differing bit.

    Attributes:
        node_id (bytes): The local node's 20-byte ID
        k (int): Maximum nodes per bucket (Kademlia parameter K)
        buckets (List[List[Node]]): 160 buckets, each containing up to K nodes
    """

    def __init__(self, node_id: bytes, k: int = 8):
        """
        Initialize the routing table.

        Args:
            node_id: The local node's 20-byte identifier
            k: Maximum nodes per bucket (default 8, typical values are 8 or 20)

        Raises:
            ValueError: If node_id is not 20 bytes
            ValueError: If k is not positive
            TypeError: If arguments have wrong types

        Examples:
            >>> table = RoutingTable(b'A' * 20)
            >>> len(table.buckets)
            160
            >>> table.k
            8

        Security Notes:
            - Validates node_id length to prevent buffer overflows
            - Validates k to prevent resource exhaustion attacks
            - Limits bucket size to prevent memory exhaustion
        """
        # Validate types
        if not isinstance(node_id, bytes):
            raise TypeError(f"node_id must be bytes, got {type(node_id)}")
        if not isinstance(k, int):
            raise TypeError(f"k must be int, got {type(k)}")

        # Validate node_id length
        if len(node_id) != 20:
            raise ValueError(f"node_id must be 20 bytes, got {len(node_id)} bytes")

        # Validate k value
        if k <= 0:
            raise ValueError(f"k must be positive, got {k}")
        if k > 100:  # Reasonable upper limit to prevent resource exhaustion
            raise ValueError(f"k too large (max 100), got {k}")

        self.node_id = node_id
        self.k = k
        # Create 160 empty buckets (one for each bit in 160-bit ID space)
        self.buckets: List[List[Node]] = [[] for _ in range(160)]

    def get_bucket_index(self, target_id: bytes) -> int:
        """
        Calculate which bucket a target node ID belongs to.

        The bucket index is determined by the position of the most significant bit
        that differs between the local node ID and the target ID. This implements
        the XOR-based distance metric used in Kademlia.

        Args:
            target_id: The 20-byte node ID to find the bucket for

        Returns:
            int: Bucket index (0-159), where 0 is closest, 159 is farthest

        Raises:
            ValueError: If target_id is not 20 bytes
            ValueError: If target_id equals local node_id
            TypeError: If target_id is not bytes

        Examples:
            >>> table = RoutingTable(b'\\x00' * 20)
            >>> # ID with only last bit different
            >>> table.get_bucket_index(b'\\x00' * 19 + b'\\x01')
            0
            >>> # ID with first byte different
            >>> table.get_bucket_index(b'\\xff' + b'\\x00' * 19)
            159

        Security Notes:
            - Validates input to prevent invalid calculations
            - Prevents self-addition by rejecting own node_id
        """
        # Validate type
        if not isinstance(target_id, bytes):
            raise TypeError(f"target_id must be bytes, got {type(target_id)}")

        # Validate length
        if len(target_id) != 20:
            raise ValueError(f"target_id must be 20 bytes, got {len(target_id)} bytes")

        # Calculate XOR distance
        dist = distance(self.node_id, target_id)

        # Can't add self to routing table
        if dist == 0:
            raise ValueError("Cannot determine bucket for own node_id")

        # Find the position of the most significant bit (0-indexed from right)
        # This tells us which bucket the node belongs to
        # bit_length() returns the number of bits needed to represent the number
        # bit_length() - 1 gives us the position of the MSB (0-indexed from right)
        # In Kademlia: bucket 0 = closest (LSB differs), bucket 159 = farthest (MSB differs)
        bucket_index = dist.bit_length() - 1

        return bucket_index

    def add_node(self, node: Node) -> bool:
        """
        Add a node to the routing table.

        Nodes are added to the appropriate bucket based on their XOR distance
        from the local node. If the bucket is full, the node may not be added
        (implementing Kademlia's preference for older, more stable nodes).

        Args:
            node: The Node object to add

        Returns:
            bool: True if node was added, False if bucket was full or node already exists

        Raises:
            TypeError: If node is not a Node object
            ValueError: If attempting to add self to routing table

        Examples:
            >>> local_id = b'A' * 20
            >>> table = RoutingTable(local_id)
            >>> node = Node(b'B' * 20, '192.168.1.1', 6881)
            >>> table.add_node(node)
            True
            >>> # Adding same node again returns False
            >>> table.add_node(node)
            False

        Security Notes:
            - Prevents self-addition to avoid routing loops
            - Limits bucket size to prevent memory exhaustion
            - Checks for duplicates to prevent amplification attacks
        """
        # Validate type
        if not isinstance(node, Node):
            raise TypeError(f"node must be Node object, got {type(node)}")

        # Don't add self to routing table
        if node.node_id == self.node_id:
            raise ValueError("Cannot add own node to routing table")

        # Determine which bucket this node belongs to
        try:
            bucket_index = self.get_bucket_index(node.node_id)
        except ValueError as e:
            # This happens if trying to add self
            raise ValueError(f"Cannot add node: {e}")

        bucket = self.buckets[bucket_index]

        # Check if node already exists in bucket
        if node in bucket:
            # Node already in bucket, move to end (LRU update)
            bucket.remove(node)
            bucket.append(node)
            return False

        # If bucket not full, add node to end
        if len(bucket) < self.k:
            bucket.append(node)
            return True

        # Bucket is full - in full Kademlia implementation, we would ping
        # the least recently seen node and potentially replace it.
        # For simplicity, we just don't add the new node (prefer old nodes)
        return False

    def remove_node(self, node: Node) -> bool:
        """
        Remove a node from the routing table.

        Args:
            node: The Node object to remove

        Returns:
            bool: True if node was removed, False if node was not in table

        Raises:
            TypeError: If node is not a Node object

        Examples:
            >>> table = RoutingTable(b'A' * 20)
            >>> node = Node(b'B' * 20, '192.168.1.1', 6881)
            >>> table.add_node(node)
            True
            >>> table.remove_node(node)
            True
            >>> table.remove_node(node)  # Already removed
            False

        Security Notes:
            - Validates input types to prevent type confusion attacks
        """
        # Validate type
        if not isinstance(node, Node):
            raise TypeError(f"node must be Node object, got {type(node)}")

        # Find the bucket
        try:
            bucket_index = self.get_bucket_index(node.node_id)
        except ValueError:
            # Node not in any bucket (possibly self)
            return False

        bucket = self.buckets[bucket_index]

        # Try to remove node from bucket
        if node in bucket:
            bucket.remove(node)
            return True

        return False

    def get_closest_nodes(self, target_id: bytes, count: int = 8) -> List[Node]:
        """
        Get the K closest nodes to a target ID.

        Searches across all buckets to find nodes closest to the target,
        sorted by XOR distance. This is used for iterative lookups in the
        Kademlia protocol.

        Args:
            target_id: The 20-byte target node ID
            count: Maximum number of nodes to return (default 8)

        Returns:
            List[Node]: Up to 'count' nodes, sorted by distance (closest first)

        Raises:
            ValueError: If target_id is not 20 bytes
            ValueError: If count is not positive
            TypeError: If arguments have wrong types

        Examples:
            >>> table = RoutingTable(b'A' * 20)
            >>> # Add some nodes
            >>> table.add_node(Node(b'B' * 20, '192.168.1.1', 6881))
            True
            >>> table.add_node(Node(b'C' * 20, '192.168.1.2', 6881))
            True
            >>> # Find closest to a target
            >>> closest = table.get_closest_nodes(b'D' * 20, count=2)
            >>> len(closest) <= 2
            True

        Security Notes:
            - Validates inputs to prevent invalid operations
            - Limits result count to prevent resource exhaustion
            - Returns sorted results for consistent behavior
        """
        # Validate types
        if not isinstance(target_id, bytes):
            raise TypeError(f"target_id must be bytes, got {type(target_id)}")
        if not isinstance(count, int):
            raise TypeError(f"count must be int, got {type(count)}")

        # Validate target_id length
        if len(target_id) != 20:
            raise ValueError(f"target_id must be 20 bytes, got {len(target_id)} bytes")

        # Validate count
        if count <= 0:
            raise ValueError(f"count must be positive, got {count}")
        if count > 1000:  # Reasonable upper limit
            raise ValueError(f"count too large (max 1000), got {count}")

        # Collect all nodes from all buckets
        all_nodes: List[Node] = []
        for bucket in self.buckets:
            all_nodes.extend(bucket)

        # If no nodes, return empty list
        if not all_nodes:
            return []

        # Sort nodes by distance to target
        # Calculate distance for each node and sort
        nodes_with_distance = [
            (node, distance(node.node_id, target_id))
            for node in all_nodes
        ]
        nodes_with_distance.sort(key=lambda x: x[1])

        # Return up to 'count' closest nodes
        closest_nodes = [node for node, dist in nodes_with_distance[:count]]

        return closest_nodes
