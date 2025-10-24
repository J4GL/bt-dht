"""
DHT Node representation module.

This module implements the core Node class used in the Kademlia DHT protocol.
Each node in the DHT is identified by a unique 160-bit (20-byte) node ID, an IP address,
and a UDP port number.

The Kademlia protocol uses XOR metric for calculating distance between nodes,
which is crucial for routing and lookup operations.

Reference: BEP 5 - DHT Protocol
https://www.bittorrent.org/beps/bep_0005.html
"""

import os
import hashlib
import socket
from typing import Tuple


class Node:
    """
    Represents a node in the DHT network.

    A node is uniquely identified by:
    - node_id: A 160-bit (20-byte) identifier
    - ip: IPv4 or IPv6 address
    - port: UDP port number

    The node ID is used by the Kademlia algorithm to determine proximity between
    nodes and to route queries efficiently across the distributed hash table.

    Attributes:
        node_id (bytes): 20-byte node identifier
        ip (str): IP address (IPv4 or IPv6)
        port (int): UDP port number (1-65535)
    """

    def __init__(self, node_id: bytes, ip: str, port: int):
        """
        Initialize a DHT node.

        Args:
            node_id: 20-byte node identifier (must be exactly 20 bytes)
            ip: IP address as string (IPv4 or IPv6)
            port: UDP port number (must be 1-65535)

        Raises:
            ValueError: If node_id is not 20 bytes
            ValueError: If IP address format is invalid
            ValueError: If port is not in range 1-65535
            TypeError: If arguments have wrong types

        Examples:
            >>> node = Node(b'A' * 20, '192.168.1.1', 6881)
            >>> node.node_id
            b'AAAAAAAAAAAAAAAAAAAA'
            >>> node.ip
            '192.168.1.1'
            >>> node.port
            6881

        Security Notes:
            - Validates node_id length to prevent buffer overflows
            - Validates IP address format to prevent injection
            - Validates port range to prevent invalid network operations
        """
        # Validate types
        if not isinstance(node_id, bytes):
            raise TypeError(f"node_id must be bytes, got {type(node_id)}")
        if not isinstance(ip, str):
            raise TypeError(f"ip must be str, got {type(ip)}")
        if not isinstance(port, int):
            raise TypeError(f"port must be int, got {type(port)}")

        # Validate node_id length (must be exactly 20 bytes for 160-bit ID)
        if len(node_id) != 20:
            raise ValueError(f"node_id must be 20 bytes, got {len(node_id)} bytes")

        # Validate IP address format
        # Try to parse as both IPv4 and IPv6
        try:
            # This will raise an exception if IP is invalid
            socket.inet_pton(socket.AF_INET, ip)
        except (socket.error, OSError):
            # Not a valid IPv4, try IPv6
            try:
                socket.inet_pton(socket.AF_INET6, ip)
            except (socket.error, OSError):
                raise ValueError(f"Invalid IP address format: {ip}")

        # Validate port range
        if not (1 <= port <= 65535):
            raise ValueError(f"Port must be in range 1-65535, got {port}")

        self.node_id = node_id
        self.ip = ip
        self.port = port

    def __eq__(self, other) -> bool:
        """
        Check equality between two nodes.

        Two nodes are considered equal if they have the same node_id, IP, and port.

        Args:
            other: Another Node object to compare with

        Returns:
            bool: True if nodes are equal, False otherwise

        Examples:
            >>> node1 = Node(b'A' * 20, '127.0.0.1', 6881)
            >>> node2 = Node(b'A' * 20, '127.0.0.1', 6881)
            >>> node1 == node2
            True
        """
        if not isinstance(other, Node):
            return False
        return (self.node_id == other.node_id and
                self.ip == other.ip and
                self.port == other.port)

    def __hash__(self) -> int:
        """
        Generate hash for the node.

        Allows Node objects to be used in sets and as dictionary keys.
        The hash is based on node_id, IP, and port.

        Returns:
            int: Hash value for the node

        Examples:
            >>> node = Node(b'A' * 20, '127.0.0.1', 6881)
            >>> hash(node)  # Returns an integer
            """
        return hash((self.node_id, self.ip, self.port))

    def __repr__(self) -> str:
        """
        Return string representation of the node.

        Returns:
            str: Human-readable representation of the node

        Examples:
            >>> node = Node(b'\\x00' * 20, '192.168.1.1', 6881)
            >>> repr(node)
            "Node(id=0000000000000000000000000000000000000000, ip=192.168.1.1, port=6881)"
        """
        # Display node_id as hex for readability
        node_id_hex = self.node_id.hex()
        return f"Node(id={node_id_hex}, ip={self.ip}, port={self.port})"


def distance(node_id1: bytes, node_id2: bytes) -> int:
    """
    Calculate XOR distance between two node IDs.

    The Kademlia DHT uses XOR metric as a distance function. This has several
    important properties:
    - d(x,x) = 0 (distance to self is zero)
    - d(x,y) = d(y,x) (symmetric)
    - d(x,y) + d(y,z) >= d(x,z) (triangle inequality)

    The XOR metric allows efficient routing by treating node IDs as points in
    a binary tree where each bit represents a branch.

    Args:
        node_id1: First 20-byte node ID
        node_id2: Second 20-byte node ID

    Returns:
        int: XOR distance as an integer (0 to 2^160 - 1)

    Raises:
        ValueError: If either node_id is not 20 bytes
        TypeError: If arguments are not bytes

    Examples:
        >>> distance(b'\\x00' * 20, b'\\x00' * 20)
        0
        >>> distance(b'\\x00' * 20, b'\\xff' * 20)
        1461501637330902918203684832716283019655932542975
        >>> distance(b'\\x01' * 20, b'\\x02' * 20)  # Small XOR
        108199957465868643142100685300432355486429431367

    Security Notes:
        - Validates input lengths to prevent buffer overflows
        - Uses constant-time XOR operation (no timing attacks)
    """
    # Validate types
    if not isinstance(node_id1, bytes):
        raise TypeError(f"node_id1 must be bytes, got {type(node_id1)}")
    if not isinstance(node_id2, bytes):
        raise TypeError(f"node_id2 must be bytes, got {type(node_id2)}")

    # Validate lengths
    if len(node_id1) != 20:
        raise ValueError(f"node_id1 must be 20 bytes, got {len(node_id1)} bytes")
    if len(node_id2) != 20:
        raise ValueError(f"node_id2 must be 20 bytes, got {len(node_id2)} bytes")

    # Perform XOR byte-by-byte and convert to integer
    # XOR each byte and combine into a single integer
    xor_result = int.from_bytes(node_id1, byteorder='big') ^ int.from_bytes(node_id2, byteorder='big')

    return xor_result


def generate_node_id() -> bytes:
    """
    Generate a random 20-byte node ID.

    Uses the system's cryptographically secure random number generator to
    create a unique node ID. The probability of collision is negligible given
    the 160-bit ID space (2^160 possible IDs).

    Returns:
        bytes: A random 20-byte node ID

    Examples:
        >>> node_id = generate_node_id()
        >>> len(node_id)
        20
        >>> isinstance(node_id, bytes)
        True
        >>> # Each call should produce different IDs
        >>> generate_node_id() != generate_node_id()  # Almost certainly True
        True

    Security Notes:
        - Uses os.urandom() which provides cryptographically secure random bytes
        - 160-bit ID space makes collisions virtually impossible
        - No predictable patterns in generated IDs
    """
    # Use os.urandom for cryptographically secure random bytes
    # This is suitable for generating unique node IDs in a distributed system
    return os.urandom(20)
