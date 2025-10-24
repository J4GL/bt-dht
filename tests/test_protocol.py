"""
Unit tests for DHT Protocol module.

This test suite validates DHT message creation and parsing functions.
"""

import unittest
import sys
import os

# Add src directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from protocol import (
    create_ping_query,
    create_find_node_query,
    create_get_peers_query,
    pack_nodes,
    unpack_nodes,
    parse_message
)


class TestCreatePingQuery(unittest.TestCase):
    """Test cases for creating ping query messages."""

    def test_create_ping_query_valid(self):
        """Test creating valid ping query."""
        transaction_id = b'aa'
        node_id = b'A' * 20

        msg = create_ping_query(transaction_id, node_id)

        self.assertIsInstance(msg, bytes)
        # Message should be bencode-encoded dictionary
        self.assertTrue(msg.startswith(b'd'))

    def test_create_ping_query_parse(self):
        """Test that created ping query can be parsed."""
        transaction_id = b'bb'
        node_id = b'B' * 20

        msg = create_ping_query(transaction_id, node_id)
        parsed = parse_message(msg)

        self.assertEqual(parsed[b'y'], b'q')  # Query type
        self.assertEqual(parsed[b'q'], b'ping')  # Ping query
        self.assertEqual(parsed[b't'], transaction_id)
        self.assertEqual(parsed[b'a'][b'id'], node_id)

    def test_create_ping_query_invalid_transaction_id_length(self):
        """Test that invalid transaction ID length raises ValueError."""
        with self.assertRaises(ValueError) as ctx:
            create_ping_query(b'a', b'A' * 20)  # Too short
        self.assertIn("2 bytes", str(ctx.exception))

        with self.assertRaises(ValueError):
            create_ping_query(b'aaa', b'A' * 20)  # Too long

    def test_create_ping_query_invalid_node_id_length(self):
        """Test that invalid node ID length raises ValueError."""
        with self.assertRaises(ValueError) as ctx:
            create_ping_query(b'aa', b'short')
        self.assertIn("20 bytes", str(ctx.exception))

    def test_create_ping_query_invalid_types(self):
        """Test that invalid types raise TypeError."""
        with self.assertRaises(TypeError):
            create_ping_query('aa', b'A' * 20)  # str instead of bytes

        with self.assertRaises(TypeError):
            create_ping_query(b'aa', 'A' * 20)  # str instead of bytes


class TestCreateFindNodeQuery(unittest.TestCase):
    """Test cases for creating find_node query messages."""

    def test_create_find_node_query_valid(self):
        """Test creating valid find_node query."""
        transaction_id = b'aa'
        node_id = b'A' * 20
        target_id = b'B' * 20

        msg = create_find_node_query(transaction_id, node_id, target_id)

        self.assertIsInstance(msg, bytes)

    def test_create_find_node_query_parse(self):
        """Test that created find_node query can be parsed."""
        transaction_id = b'cc'
        node_id = b'C' * 20
        target_id = b'D' * 20

        msg = create_find_node_query(transaction_id, node_id, target_id)
        parsed = parse_message(msg)

        self.assertEqual(parsed[b'y'], b'q')
        self.assertEqual(parsed[b'q'], b'find_node')
        self.assertEqual(parsed[b't'], transaction_id)
        self.assertEqual(parsed[b'a'][b'id'], node_id)
        self.assertEqual(parsed[b'a'][b'target'], target_id)

    def test_create_find_node_query_invalid_lengths(self):
        """Test that invalid lengths raise ValueError."""
        # Invalid transaction_id
        with self.assertRaises(ValueError):
            create_find_node_query(b'a', b'A' * 20, b'B' * 20)

        # Invalid node_id
        with self.assertRaises(ValueError):
            create_find_node_query(b'aa', b'short', b'B' * 20)

        # Invalid target_id
        with self.assertRaises(ValueError):
            create_find_node_query(b'aa', b'A' * 20, b'short')

    def test_create_find_node_query_invalid_types(self):
        """Test that invalid types raise TypeError."""
        with self.assertRaises(TypeError):
            create_find_node_query('aa', b'A' * 20, b'B' * 20)

        with self.assertRaises(TypeError):
            create_find_node_query(b'aa', 'A' * 20, b'B' * 20)

        with self.assertRaises(TypeError):
            create_find_node_query(b'aa', b'A' * 20, 'B' * 20)


class TestCreateGetPeersQuery(unittest.TestCase):
    """Test cases for creating get_peers query messages."""

    def test_create_get_peers_query_valid(self):
        """Test creating valid get_peers query."""
        transaction_id = b'aa'
        node_id = b'A' * 20
        info_hash = b'H' * 20

        msg = create_get_peers_query(transaction_id, node_id, info_hash)

        self.assertIsInstance(msg, bytes)

    def test_create_get_peers_query_parse(self):
        """Test that created get_peers query can be parsed."""
        transaction_id = b'dd'
        node_id = b'D' * 20
        info_hash = b'I' * 20

        msg = create_get_peers_query(transaction_id, node_id, info_hash)
        parsed = parse_message(msg)

        self.assertEqual(parsed[b'y'], b'q')
        self.assertEqual(parsed[b'q'], b'get_peers')
        self.assertEqual(parsed[b't'], transaction_id)
        self.assertEqual(parsed[b'a'][b'id'], node_id)
        self.assertEqual(parsed[b'a'][b'info_hash'], info_hash)

    def test_create_get_peers_query_invalid_lengths(self):
        """Test that invalid lengths raise ValueError."""
        # Invalid transaction_id
        with self.assertRaises(ValueError):
            create_get_peers_query(b'a', b'A' * 20, b'H' * 20)

        # Invalid node_id
        with self.assertRaises(ValueError):
            create_get_peers_query(b'aa', b'short', b'H' * 20)

        # Invalid info_hash
        with self.assertRaises(ValueError):
            create_get_peers_query(b'aa', b'A' * 20, b'short')

    def test_create_get_peers_query_invalid_types(self):
        """Test that invalid types raise TypeError."""
        with self.assertRaises(TypeError):
            create_get_peers_query('aa', b'A' * 20, b'H' * 20)

        with self.assertRaises(TypeError):
            create_get_peers_query(b'aa', 'A' * 20, b'H' * 20)

        with self.assertRaises(TypeError):
            create_get_peers_query(b'aa', b'A' * 20, 'H' * 20)


class TestPackNodes(unittest.TestCase):
    """Test cases for packing nodes into compact format."""

    def test_pack_nodes_single(self):
        """Test packing single node."""
        nodes = [(b'A' * 20, '192.168.1.1', 6881)]
        packed = pack_nodes(nodes)

        # Should be 26 bytes (20 + 4 + 2)
        self.assertEqual(len(packed), 26)
        self.assertIsInstance(packed, bytes)

    def test_pack_nodes_multiple(self):
        """Test packing multiple nodes."""
        nodes = [
            (b'A' * 20, '192.168.1.1', 6881),
            (b'B' * 20, '192.168.1.2', 6882),
            (b'C' * 20, '192.168.1.3', 6883),
        ]
        packed = pack_nodes(nodes)

        # Should be 78 bytes (3 * 26)
        self.assertEqual(len(packed), 78)

    def test_pack_nodes_empty(self):
        """Test packing empty node list."""
        packed = pack_nodes([])
        self.assertEqual(len(packed), 0)

    def test_pack_nodes_invalid_node_id_length(self):
        """Test that invalid node_id length raises ValueError."""
        nodes = [(b'short', '192.168.1.1', 6881)]
        with self.assertRaises(ValueError) as ctx:
            pack_nodes(nodes)
        self.assertIn("20 bytes", str(ctx.exception))

    def test_pack_nodes_invalid_ip(self):
        """Test that invalid IP address raises ValueError."""
        nodes = [(b'A' * 20, 'invalid-ip', 6881)]
        with self.assertRaises(ValueError) as ctx:
            pack_nodes(nodes)
        self.assertIn("Invalid IPv4", str(ctx.exception))

    def test_pack_nodes_invalid_port(self):
        """Test that invalid port raises ValueError."""
        nodes = [(b'A' * 20, '192.168.1.1', 0)]
        with self.assertRaises(ValueError) as ctx:
            pack_nodes(nodes)
        self.assertIn("1-65535", str(ctx.exception))

        nodes = [(b'A' * 20, '192.168.1.1', 65536)]
        with self.assertRaises(ValueError):
            pack_nodes(nodes)

    def test_pack_nodes_invalid_structure(self):
        """Test that invalid node structure raises ValueError."""
        # Not a tuple
        with self.assertRaises(ValueError):
            pack_nodes(['not a tuple'])

        # Wrong number of elements
        with self.assertRaises(ValueError):
            pack_nodes([(b'A' * 20, '192.168.1.1')])  # Missing port

    def test_pack_nodes_invalid_type(self):
        """Test that invalid types raise TypeError."""
        with self.assertRaises(TypeError):
            pack_nodes('not a list')


class TestUnpackNodes(unittest.TestCase):
    """Test cases for unpacking nodes from compact format."""

    def test_unpack_nodes_single(self):
        """Test unpacking single node."""
        # Pack then unpack
        original = [(b'A' * 20, '192.168.1.1', 6881)]
        packed = pack_nodes(original)
        unpacked = unpack_nodes(packed)

        self.assertEqual(len(unpacked), 1)
        self.assertEqual(unpacked[0], original[0])

    def test_unpack_nodes_multiple(self):
        """Test unpacking multiple nodes."""
        original = [
            (b'A' * 20, '192.168.1.1', 6881),
            (b'B' * 20, '10.0.0.1', 6882),
            (b'C' * 20, '172.16.0.1', 6883),
        ]
        packed = pack_nodes(original)
        unpacked = unpack_nodes(packed)

        self.assertEqual(len(unpacked), 3)
        for i, node in enumerate(unpacked):
            self.assertEqual(node, original[i])

    def test_unpack_nodes_empty(self):
        """Test unpacking empty data."""
        unpacked = unpack_nodes(b'')
        self.assertEqual(len(unpacked), 0)

    def test_unpack_nodes_invalid_length(self):
        """Test that invalid data length raises ValueError."""
        # Not a multiple of 26
        with self.assertRaises(ValueError) as ctx:
            unpack_nodes(b'A' * 25)
        self.assertIn("multiple of 26", str(ctx.exception))

        with self.assertRaises(ValueError):
            unpack_nodes(b'A' * 27)

    def test_unpack_nodes_invalid_type(self):
        """Test that invalid type raises TypeError."""
        with self.assertRaises(TypeError):
            unpack_nodes('not bytes')

    def test_unpack_nodes_roundtrip(self):
        """Test pack/unpack roundtrip preserves data."""
        original = [
            (b'\x00' * 20, '127.0.0.1', 1),
            (b'\xff' * 20, '255.255.255.255', 65535),
            (b'\x55' * 20, '192.168.0.1', 8080),
        ]

        packed = pack_nodes(original)
        unpacked = unpack_nodes(packed)

        self.assertEqual(unpacked, original)


class TestParseMessage(unittest.TestCase):
    """Test cases for parsing DHT messages."""

    def test_parse_message_ping_query(self):
        """Test parsing ping query message."""
        msg = create_ping_query(b'aa', b'A' * 20)
        parsed = parse_message(msg)

        self.assertIsInstance(parsed, dict)
        self.assertEqual(parsed[b'y'], b'q')
        self.assertEqual(parsed[b'q'], b'ping')

    def test_parse_message_find_node_query(self):
        """Test parsing find_node query message."""
        msg = create_find_node_query(b'bb', b'B' * 20, b'C' * 20)
        parsed = parse_message(msg)

        self.assertEqual(parsed[b'y'], b'q')
        self.assertEqual(parsed[b'q'], b'find_node')

    def test_parse_message_get_peers_query(self):
        """Test parsing get_peers query message."""
        msg = create_get_peers_query(b'cc', b'C' * 20, b'H' * 20)
        parsed = parse_message(msg)

        self.assertEqual(parsed[b'y'], b'q')
        self.assertEqual(parsed[b'q'], b'get_peers')

    def test_parse_message_invalid_bencode(self):
        """Test that invalid bencode raises ValueError."""
        with self.assertRaises(ValueError) as ctx:
            parse_message(b'not bencode')
        self.assertIn("Invalid bencode", str(ctx.exception))

    def test_parse_message_not_dictionary(self):
        """Test that non-dictionary message raises ValueError."""
        from bencode import encode
        # Encode a list instead of dict
        with self.assertRaises(ValueError) as ctx:
            parse_message(encode([1, 2, 3]))
        self.assertIn("dictionary", str(ctx.exception))

    def test_parse_message_missing_type_field(self):
        """Test that message without 'y' field raises ValueError."""
        from bencode import encode
        msg = encode({b't': b'aa', b'q': b'ping'})  # Missing 'y'
        with self.assertRaises(ValueError) as ctx:
            parse_message(msg)
        self.assertIn("'y'", str(ctx.exception))

    def test_parse_message_invalid_type(self):
        """Test that invalid message type raises ValueError."""
        from bencode import encode
        msg = encode({b'y': b'x', b't': b'aa'})  # Invalid type 'x'
        with self.assertRaises(ValueError) as ctx:
            parse_message(msg)
        self.assertIn("Invalid message type", str(ctx.exception))

    def test_parse_message_missing_transaction_id(self):
        """Test that message without transaction ID raises ValueError."""
        from bencode import encode
        msg = encode({b'y': b'q', b'q': b'ping'})  # Missing 't'
        with self.assertRaises(ValueError) as ctx:
            parse_message(msg)
        self.assertIn("'t'", str(ctx.exception))

    def test_parse_message_invalid_type_arg(self):
        """Test that non-bytes input raises TypeError."""
        with self.assertRaises(TypeError):
            parse_message('not bytes')


if __name__ == '__main__':
    # Run tests with verbose output
    unittest.main(verbosity=2)
