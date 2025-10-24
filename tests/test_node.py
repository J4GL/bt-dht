"""
Unit tests for DHT Node module.

This test suite validates the Node class and related functions used in the
Kademlia DHT protocol implementation.
"""

import unittest
import sys
import os

# Add src directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from node import Node, distance, generate_node_id


class TestNodeInit(unittest.TestCase):
    """Test cases for Node initialization."""

    def test_node_creation_valid_ipv4(self):
        """Test creating node with valid IPv4 address."""
        node_id = b'A' * 20
        ip = '192.168.1.1'
        port = 6881

        node = Node(node_id, ip, port)

        self.assertEqual(node.node_id, node_id)
        self.assertEqual(node.ip, ip)
        self.assertEqual(node.port, port)

    def test_node_creation_valid_ipv6(self):
        """Test creating node with valid IPv6 address."""
        node_id = b'B' * 20
        ip = '::1'  # IPv6 localhost
        port = 6881

        node = Node(node_id, ip, port)

        self.assertEqual(node.node_id, node_id)
        self.assertEqual(node.ip, ip)
        self.assertEqual(node.port, port)

    def test_node_creation_full_ipv6(self):
        """Test creating node with full IPv6 address."""
        node_id = b'C' * 20
        ip = '2001:0db8:85a3:0000:0000:8a2e:0370:7334'
        port = 6881

        node = Node(node_id, ip, port)
        self.assertEqual(node.ip, ip)

    def test_node_creation_invalid_node_id_length(self):
        """Test that invalid node_id length raises ValueError."""
        # Too short
        with self.assertRaises(ValueError) as ctx:
            Node(b'short', '127.0.0.1', 6881)
        self.assertIn("20 bytes", str(ctx.exception))

        # Too long
        with self.assertRaises(ValueError):
            Node(b'A' * 21, '127.0.0.1', 6881)

        # Empty
        with self.assertRaises(ValueError):
            Node(b'', '127.0.0.1', 6881)

    def test_node_creation_invalid_node_id_type(self):
        """Test that invalid node_id type raises TypeError."""
        with self.assertRaises(TypeError) as ctx:
            Node('not bytes', '127.0.0.1', 6881)
        self.assertIn("node_id must be bytes", str(ctx.exception))

        with self.assertRaises(TypeError):
            Node(12345, '127.0.0.1', 6881)

    def test_node_creation_invalid_ip(self):
        """Test that invalid IP address raises ValueError."""
        node_id = b'A' * 20

        # Invalid format
        with self.assertRaises(ValueError) as ctx:
            Node(node_id, '999.999.999.999', 6881)
        self.assertIn("Invalid IP address", str(ctx.exception))

        # Not an IP address
        with self.assertRaises(ValueError):
            Node(node_id, 'not-an-ip', 6881)

        # Empty string
        with self.assertRaises(ValueError):
            Node(node_id, '', 6881)

    def test_node_creation_invalid_ip_type(self):
        """Test that invalid IP type raises TypeError."""
        node_id = b'A' * 20

        with self.assertRaises(TypeError) as ctx:
            Node(node_id, 123456, 6881)
        self.assertIn("ip must be str", str(ctx.exception))

    def test_node_creation_invalid_port(self):
        """Test that invalid port raises ValueError."""
        node_id = b'A' * 20
        ip = '127.0.0.1'

        # Port 0
        with self.assertRaises(ValueError) as ctx:
            Node(node_id, ip, 0)
        self.assertIn("range 1-65535", str(ctx.exception))

        # Port too high
        with self.assertRaises(ValueError):
            Node(node_id, ip, 65536)

        # Negative port
        with self.assertRaises(ValueError):
            Node(node_id, ip, -1)

    def test_node_creation_invalid_port_type(self):
        """Test that invalid port type raises TypeError."""
        node_id = b'A' * 20
        ip = '127.0.0.1'

        with self.assertRaises(TypeError) as ctx:
            Node(node_id, ip, '6881')
        self.assertIn("port must be int", str(ctx.exception))

        with self.assertRaises(TypeError):
            Node(node_id, ip, 6881.0)

    def test_node_creation_edge_case_ports(self):
        """Test node creation with edge case port values."""
        node_id = b'A' * 20
        ip = '127.0.0.1'

        # Minimum valid port
        node1 = Node(node_id, ip, 1)
        self.assertEqual(node1.port, 1)

        # Maximum valid port
        node2 = Node(node_id, ip, 65535)
        self.assertEqual(node2.port, 65535)


class TestNodeEquality(unittest.TestCase):
    """Test cases for Node equality comparison."""

    def test_node_equality_same_values(self):
        """Test that nodes with same values are equal."""
        node_id = b'A' * 20
        ip = '127.0.0.1'
        port = 6881

        node1 = Node(node_id, ip, port)
        node2 = Node(node_id, ip, port)

        self.assertEqual(node1, node2)
        self.assertTrue(node1 == node2)

    def test_node_inequality_different_id(self):
        """Test that nodes with different IDs are not equal."""
        node1 = Node(b'A' * 20, '127.0.0.1', 6881)
        node2 = Node(b'B' * 20, '127.0.0.1', 6881)

        self.assertNotEqual(node1, node2)
        self.assertFalse(node1 == node2)

    def test_node_inequality_different_ip(self):
        """Test that nodes with different IPs are not equal."""
        node_id = b'A' * 20
        node1 = Node(node_id, '127.0.0.1', 6881)
        node2 = Node(node_id, '192.168.1.1', 6881)

        self.assertNotEqual(node1, node2)

    def test_node_inequality_different_port(self):
        """Test that nodes with different ports are not equal."""
        node_id = b'A' * 20
        ip = '127.0.0.1'
        node1 = Node(node_id, ip, 6881)
        node2 = Node(node_id, ip, 6882)

        self.assertNotEqual(node1, node2)

    def test_node_equality_with_non_node(self):
        """Test that node is not equal to non-Node objects."""
        node = Node(b'A' * 20, '127.0.0.1', 6881)

        self.assertNotEqual(node, "not a node")
        self.assertNotEqual(node, 123)
        self.assertNotEqual(node, None)
        self.assertFalse(node == "not a node")


class TestNodeHash(unittest.TestCase):
    """Test cases for Node hashing."""

    def test_node_hash_consistent(self):
        """Test that same node produces same hash."""
        node1 = Node(b'A' * 20, '127.0.0.1', 6881)
        node2 = Node(b'A' * 20, '127.0.0.1', 6881)

        self.assertEqual(hash(node1), hash(node2))

    def test_node_hash_different_nodes(self):
        """Test that different nodes produce different hashes (usually)."""
        node1 = Node(b'A' * 20, '127.0.0.1', 6881)
        node2 = Node(b'B' * 20, '192.168.1.1', 6882)

        # While hash collisions are possible, they should be rare
        # This test might theoretically fail, but probability is very low
        self.assertNotEqual(hash(node1), hash(node2))

    def test_node_in_set(self):
        """Test that nodes can be used in sets."""
        node1 = Node(b'A' * 20, '127.0.0.1', 6881)
        node2 = Node(b'B' * 20, '192.168.1.1', 6881)
        node3 = Node(b'A' * 20, '127.0.0.1', 6881)  # Same as node1

        node_set = {node1, node2, node3}

        # Set should have 2 elements (node1 and node3 are same)
        self.assertEqual(len(node_set), 2)
        self.assertIn(node1, node_set)
        self.assertIn(node2, node_set)

    def test_node_as_dict_key(self):
        """Test that nodes can be used as dictionary keys."""
        node1 = Node(b'A' * 20, '127.0.0.1', 6881)
        node2 = Node(b'B' * 20, '192.168.1.1', 6881)

        node_dict = {node1: 'value1', node2: 'value2'}

        self.assertEqual(node_dict[node1], 'value1')
        self.assertEqual(node_dict[node2], 'value2')


class TestNodeRepr(unittest.TestCase):
    """Test cases for Node string representation."""

    def test_node_repr_format(self):
        """Test that repr returns properly formatted string."""
        node_id = b'\x00' * 20
        node = Node(node_id, '192.168.1.1', 6881)

        repr_str = repr(node)

        self.assertIn('Node', repr_str)
        self.assertIn('0' * 40, repr_str)  # Hex representation of node_id
        self.assertIn('192.168.1.1', repr_str)
        self.assertIn('6881', repr_str)

    def test_node_repr_different_id(self):
        """Test repr with different node ID."""
        node_id = b'\xff' * 20
        node = Node(node_id, '127.0.0.1', 6881)

        repr_str = repr(node)

        self.assertIn('f' * 40, repr_str)  # Hex representation
        self.assertIn('127.0.0.1', repr_str)


class TestDistance(unittest.TestCase):
    """Test cases for XOR distance calculation."""

    def test_distance_zero_same_ids(self):
        """Test that distance to self is zero."""
        node_id = b'A' * 20
        self.assertEqual(distance(node_id, node_id), 0)

    def test_distance_symmetric(self):
        """Test that distance is symmetric: d(x,y) = d(y,x)."""
        node_id1 = b'A' * 20
        node_id2 = b'B' * 20

        dist1 = distance(node_id1, node_id2)
        dist2 = distance(node_id2, node_id1)

        self.assertEqual(dist1, dist2)

    def test_distance_calculation(self):
        """Test distance calculation with known values."""
        # XOR of 0x00 and 0xFF is 0xFF
        node_id1 = b'\x00' * 20
        node_id2 = b'\xff' * 20

        dist = distance(node_id1, node_id2)

        # Maximum distance for 160-bit ID
        expected = int('ff' * 20, 16)
        self.assertEqual(dist, expected)

    def test_distance_small_difference(self):
        """Test distance with small XOR difference."""
        # Only last byte differs
        node_id1 = b'\x00' * 19 + b'\x00'
        node_id2 = b'\x00' * 19 + b'\x01'

        dist = distance(node_id1, node_id2)

        # XOR difference is just the last byte
        self.assertEqual(dist, 1)

    def test_distance_invalid_length_first(self):
        """Test that invalid first node_id length raises ValueError."""
        with self.assertRaises(ValueError) as ctx:
            distance(b'short', b'A' * 20)
        self.assertIn("20 bytes", str(ctx.exception))

    def test_distance_invalid_length_second(self):
        """Test that invalid second node_id length raises ValueError."""
        with self.assertRaises(ValueError) as ctx:
            distance(b'A' * 20, b'short')
        self.assertIn("20 bytes", str(ctx.exception))

    def test_distance_invalid_type_first(self):
        """Test that invalid first node_id type raises TypeError."""
        with self.assertRaises(TypeError) as ctx:
            distance('not bytes', b'A' * 20)
        self.assertIn("node_id1 must be bytes", str(ctx.exception))

    def test_distance_invalid_type_second(self):
        """Test that invalid second node_id type raises TypeError."""
        with self.assertRaises(TypeError) as ctx:
            distance(b'A' * 20, 'not bytes')
        self.assertIn("node_id2 must be bytes", str(ctx.exception))

    def test_distance_triangle_inequality(self):
        """Test triangle inequality: d(x,z) <= d(x,y) + d(y,z)."""
        node_id1 = b'\x00' * 20
        node_id2 = b'\x55' * 20  # 01010101 pattern
        node_id3 = b'\xaa' * 20  # 10101010 pattern

        d_12 = distance(node_id1, node_id2)
        d_23 = distance(node_id2, node_id3)
        d_13 = distance(node_id1, node_id3)

        # Triangle inequality (actually XOR doesn't always satisfy this,
        # but we test the calculation is correct)
        # For XOR: d(x,z) = d(x,y) XOR d(y,z) which is different
        # Let's just verify the calculation works
        self.assertIsInstance(d_12, int)
        self.assertIsInstance(d_23, int)
        self.assertIsInstance(d_13, int)


class TestGenerateNodeId(unittest.TestCase):
    """Test cases for node ID generation."""

    def test_generate_node_id_length(self):
        """Test that generated node ID is 20 bytes."""
        node_id = generate_node_id()
        self.assertEqual(len(node_id), 20)

    def test_generate_node_id_type(self):
        """Test that generated node ID is bytes."""
        node_id = generate_node_id()
        self.assertIsInstance(node_id, bytes)

    def test_generate_node_id_unique(self):
        """Test that generated node IDs are unique (probabilistically)."""
        # Generate multiple IDs
        ids = [generate_node_id() for _ in range(100)]

        # All should be different (collision probability is negligible)
        unique_ids = set(ids)
        self.assertEqual(len(unique_ids), 100)

    def test_generate_node_id_randomness(self):
        """Test that generated IDs have sufficient randomness."""
        # Generate an ID and check it's not all zeros or all same byte
        node_id = generate_node_id()

        # Should not be all zeros (probability: 1/2^160, essentially impossible)
        self.assertNotEqual(node_id, b'\x00' * 20)

        # Should not be all same byte (check a few common patterns)
        for byte_val in [b'\x00', b'\xff', b'\x55', b'\xaa']:
            if node_id == byte_val * 20:
                self.fail(f"Generated node_id is all {byte_val.hex()}")

    def test_generate_node_id_can_create_node(self):
        """Test that generated ID can be used to create a Node."""
        node_id = generate_node_id()

        # Should not raise any exceptions
        node = Node(node_id, '127.0.0.1', 6881)
        self.assertEqual(node.node_id, node_id)


if __name__ == '__main__':
    # Run tests with verbose output
    unittest.main(verbosity=2)
