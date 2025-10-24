"""
DHT Protocol message handling module.

This module implements creation and parsing of DHT protocol messages according to BEP 5.
The DHT protocol uses bencode-encoded dictionaries sent over UDP.

Message types:
- Queries (q): ping, find_node, get_peers, announce_peer
- Responses (r): Response data
- Errors (e): Error information

Reference: BEP 5 - DHT Protocol
https://www.bittorrent.org/beps/bep_0005.html
"""

import struct
import socket
from typing import Dict, List, Tuple, Any, Optional
from bencode import encode, decode


def create_ping_query(transaction_id: bytes, node_id: bytes) -> bytes:
    """
    Create a ping query message.

    Ping is used to check if a node is still alive.

    Args:
        transaction_id: 2-byte transaction ID for matching requests/responses
        node_id: 20-byte ID of the querying node

    Returns:
        bytes: Bencode-encoded ping query message

    Raises:
        ValueError: If transaction_id is not 2 bytes or node_id is not 20 bytes
        TypeError: If arguments have wrong types

    Examples:
        >>> msg = create_ping_query(b'aa', b'A' * 20)
        >>> isinstance(msg, bytes)
        True

    Security Notes:
        - Validates input lengths to prevent malformed messages
        - Uses bencode encoding to prevent injection attacks
    """
    # Validate types
    if not isinstance(transaction_id, bytes):
        raise TypeError("transaction_id must be bytes")
    if not isinstance(node_id, bytes):
        raise TypeError("node_id must be bytes")

    # Validate lengths
    if len(transaction_id) != 2:
        raise ValueError(f"transaction_id must be 2 bytes, got {len(transaction_id)}")
    if len(node_id) != 20:
        raise ValueError(f"node_id must be 20 bytes, got {len(node_id)}")

    message = {
        b't': transaction_id,
        b'y': b'q',  # Query
        b'q': b'ping',  # Query type
        b'a': {b'id': node_id}  # Arguments
    }

    return encode(message)


def create_find_node_query(transaction_id: bytes, node_id: bytes, target_id: bytes) -> bytes:
    """
    Create a find_node query message.

    Find_node is used to find nodes close to a target ID.

    Args:
        transaction_id: 2-byte transaction ID
        node_id: 20-byte ID of the querying node
        target_id: 20-byte target node ID to search for

    Returns:
        bytes: Bencode-encoded find_node query message

    Raises:
        ValueError: If any ID has incorrect length
        TypeError: If arguments have wrong types

    Examples:
        >>> msg = create_find_node_query(b'aa', b'A' * 20, b'B' * 20)
        >>> isinstance(msg, bytes)
        True

    Security Notes:
        - Validates all input lengths
        - Prevents injection through bencode encoding
    """
    # Validate types
    if not isinstance(transaction_id, bytes):
        raise TypeError("transaction_id must be bytes")
    if not isinstance(node_id, bytes):
        raise TypeError("node_id must be bytes")
    if not isinstance(target_id, bytes):
        raise TypeError("target_id must be bytes")

    # Validate lengths
    if len(transaction_id) != 2:
        raise ValueError(f"transaction_id must be 2 bytes, got {len(transaction_id)}")
    if len(node_id) != 20:
        raise ValueError(f"node_id must be 20 bytes, got {len(node_id)}")
    if len(target_id) != 20:
        raise ValueError(f"target_id must be 20 bytes, got {len(target_id)}")

    message = {
        b't': transaction_id,
        b'y': b'q',
        b'q': b'find_node',
        b'a': {b'id': node_id, b'target': target_id}
    }

    return encode(message)


def create_get_peers_query(transaction_id: bytes, node_id: bytes, info_hash: bytes) -> bytes:
    """
    Create a get_peers query message.

    Get_peers is used to find peers for a torrent with the given info_hash.

    Args:
        transaction_id: 2-byte transaction ID
        node_id: 20-byte ID of the querying node
        info_hash: 20-byte info hash of the torrent

    Returns:
        bytes: Bencode-encoded get_peers query message

    Raises:
        ValueError: If any ID has incorrect length
        TypeError: If arguments have wrong types

    Examples:
        >>> msg = create_get_peers_query(b'aa', b'A' * 20, b'H' * 20)
        >>> isinstance(msg, bytes)
        True

    Security Notes:
        - Validates all input lengths
        - Prevents injection attacks through validation
    """
    # Validate types
    if not isinstance(transaction_id, bytes):
        raise TypeError("transaction_id must be bytes")
    if not isinstance(node_id, bytes):
        raise TypeError("node_id must be bytes")
    if not isinstance(info_hash, bytes):
        raise TypeError("info_hash must be bytes")

    # Validate lengths
    if len(transaction_id) != 2:
        raise ValueError(f"transaction_id must be 2 bytes, got {len(transaction_id)}")
    if len(node_id) != 20:
        raise ValueError(f"node_id must be 20 bytes, got {len(node_id)}")
    if len(info_hash) != 20:
        raise ValueError(f"info_hash must be 20 bytes, got {len(info_hash)}")

    message = {
        b't': transaction_id,
        b'y': b'q',
        b'q': b'get_peers',
        b'a': {b'id': node_id, b'info_hash': info_hash}
    }

    return encode(message)


def pack_nodes(nodes: List[Tuple[bytes, str, int]]) -> bytes:
    """
    Pack a list of nodes into compact format.

    Compact node format (IPv4): 26 bytes per node
    - 20 bytes: node ID
    - 4 bytes: IP address
    - 2 bytes: port (big-endian)

    Args:
        nodes: List of tuples (node_id, ip_address, port)

    Returns:
        bytes: Packed nodes in compact format

    Raises:
        ValueError: If any node has invalid format
        TypeError: If arguments have wrong types

    Examples:
        >>> nodes = [(b'A' * 20, '192.168.1.1', 6881)]
        >>> packed = pack_nodes(nodes)
        >>> len(packed)
        26

    Security Notes:
        - Validates all node data before packing
        - Prevents buffer overflows through length validation
    """
    if not isinstance(nodes, list):
        raise TypeError("nodes must be a list")

    result = b''
    for node_data in nodes:
        if not isinstance(node_data, tuple) or len(node_data) != 3:
            raise ValueError("Each node must be a tuple of (node_id, ip, port)")

        node_id, ip, port = node_data

        # Validate node_id
        if not isinstance(node_id, bytes) or len(node_id) != 20:
            raise ValueError(f"node_id must be 20 bytes, got {len(node_id) if isinstance(node_id, bytes) else 'non-bytes'}")

        # Validate and pack IP
        if not isinstance(ip, str):
            raise TypeError("IP must be string")
        try:
            ip_packed = socket.inet_aton(ip)  # Convert IPv4 string to 4 bytes
        except (socket.error, OSError):
            raise ValueError(f"Invalid IPv4 address: {ip}")

        # Validate and pack port
        if not isinstance(port, int):
            raise TypeError("port must be int")
        if not (1 <= port <= 65535):
            raise ValueError(f"port must be 1-65535, got {port}")

        port_packed = struct.pack('!H', port)  # Pack as big-endian unsigned short

        # Combine: node_id (20) + IP (4) + port (2) = 26 bytes
        result += node_id + ip_packed + port_packed

    return result


def unpack_nodes(data: bytes) -> List[Tuple[bytes, str, int]]:
    """
    Unpack nodes from compact format.

    Args:
        data: Packed nodes data (must be multiple of 26 bytes)

    Returns:
        List of tuples (node_id, ip_address, port)

    Raises:
        ValueError: If data length is not a multiple of 26
        TypeError: If data is not bytes

    Examples:
        >>> # Pack and unpack roundtrip
        >>> nodes = [(b'A' * 20, '192.168.1.1', 6881)]
        >>> packed = pack_nodes(nodes)
        >>> unpacked = unpack_nodes(packed)
        >>> unpacked[0] == nodes[0]
        True

    Security Notes:
        - Validates data length to prevent buffer overruns
        - Handles malformed data gracefully
    """
    if not isinstance(data, bytes):
        raise TypeError("data must be bytes")

    if len(data) % 26 != 0:
        raise ValueError(f"data length must be multiple of 26, got {len(data)}")

    nodes = []
    for i in range(0, len(data), 26):
        # Extract node_id (20 bytes)
        node_id = data[i:i+20]

        # Extract IP (4 bytes)
        ip_packed = data[i+20:i+24]
        ip = socket.inet_ntoa(ip_packed)  # Convert 4 bytes to IPv4 string

        # Extract port (2 bytes)
        port_packed = data[i+24:i+26]
        port = struct.unpack('!H', port_packed)[0]  # Unpack big-endian unsigned short

        nodes.append((node_id, ip, port))

    return nodes


def parse_message(data: bytes) -> Dict[bytes, Any]:
    """
    Parse a DHT message from bencode-encoded bytes.

    Args:
        data: Bencode-encoded message

    Returns:
        dict: Parsed message dictionary

    Raises:
        ValueError: If message is malformed or invalid bencode
        TypeError: If data is not bytes

    Examples:
        >>> msg = create_ping_query(b'aa', b'A' * 20)
        >>> parsed = parse_message(msg)
        >>> parsed[b'y']
        b'q'
        >>> parsed[b'q']
        b'ping'

    Security Notes:
        - Validates bencode structure
        - Checks for required fields
        - Prevents malformed message attacks
    """
    if not isinstance(data, bytes):
        raise TypeError("data must be bytes")

    # Decode bencode
    try:
        message, _ = decode(data)
    except (ValueError, TypeError) as e:
        raise ValueError(f"Invalid bencode in message: {e}")

    # Validate message is a dictionary
    if not isinstance(message, dict):
        raise ValueError("Message must be a dictionary")

    # Validate required field 'y' (message type)
    if b'y' not in message:
        raise ValueError("Message missing required field 'y' (message type)")

    msg_type = message[b'y']
    if msg_type not in [b'q', b'r', b'e']:
        raise ValueError(f"Invalid message type: {msg_type}")

    # Validate required field 't' (transaction ID)
    if b't' not in message:
        raise ValueError("Message missing required field 't' (transaction ID)")

    return message


if __name__ == '__main__':
    # Quick test
    msg = create_ping_query(b'aa', b'A' * 20)
    parsed = parse_message(msg)
    print(f"Created and parsed ping query: {parsed}")
