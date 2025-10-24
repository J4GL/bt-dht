"""
Unit tests for Kademlia Routing Table module.

This test suite validates the routing table implementation used in the DHT.
"""

import unittest
import sys
import os

# Add src directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from routing_table import RoutingTable
from node import Node


class TestRoutingTableInit(unittest.TestCase):
    """Test cases for RoutingTable initialization."""

    def test_init_valid(self):
        """Test creating routing table with valid parameters."""
        node_id = b'A' * 20
        table = RoutingTable(node_id)

        self.assertEqual(table.node_id, node_id)
        self.assertEqual(table.k, 8)  # Default value
        self.assertEqual(len(table.buckets), 160)

    def test_init_custom_k(self):
        """Test creating routing table with custom K value."""
        node_id = b'A' * 20
        table = RoutingTable(node_id, k=20)

        self.assertEqual(table.k, 20)

    def test_init_invalid_node_id_length(self):
        """Test that invalid node_id length raises ValueError."""
        with self.assertRaises(ValueError) as ctx:
            RoutingTable(b'short')
        self.assertIn("20 bytes", str(ctx.exception))

    def test_init_invalid_node_id_type(self):
        """Test that invalid node_id type raises TypeError."""
        with self.assertRaises(TypeError) as ctx:
            RoutingTable('not bytes')
        self.assertIn("node_id must be bytes", str(ctx.exception))

    def test_init_invalid_k_value(self):
        """Test that invalid K value raises ValueError."""
        node_id = b'A' * 20

        # Zero K
        with self.assertRaises(ValueError) as ctx:
            RoutingTable(node_id, k=0)
        self.assertIn("positive", str(ctx.exception))

        # Negative K
        with self.assertRaises(ValueError):
            RoutingTable(node_id, k=-1)

        # Too large K
        with self.assertRaises(ValueError) as ctx:
            RoutingTable(node_id, k=101)
        self.assertIn("too large", str(ctx.exception))

    def test_init_invalid_k_type(self):
        """Test that invalid K type raises TypeError."""
        node_id = b'A' * 20

        with self.assertRaises(TypeError) as ctx:
            RoutingTable(node_id, k='8')
        self.assertIn("k must be int", str(ctx.exception))

    def test_init_buckets_empty(self):
        """Test that all buckets start empty."""
        table = RoutingTable(b'A' * 20)

        for bucket in table.buckets:
            self.assertEqual(len(bucket), 0)
            self.assertIsInstance(bucket, list)


class TestGetBucketIndex(unittest.TestCase):
    """Test cases for bucket index calculation."""

    def test_bucket_index_closest(self):
        """Test bucket index for closest possible node (last bit different)."""
        table = RoutingTable(b'\x00' * 20)

        # Only last bit different
        target = b'\x00' * 19 + b'\x01'
        index = table.get_bucket_index(target)

        # Closest bucket (LSB different)
        self.assertEqual(index, 0)

    def test_bucket_index_farthest(self):
        """Test bucket index for farthest possible node (first bit different)."""
        table = RoutingTable(b'\x00' * 20)

        # First bit different (MSB)
        target = b'\x80' + b'\x00' * 19  # 10000000...
        index = table.get_bucket_index(target)

        # Farthest bucket (MSB different)
        self.assertEqual(index, 159)

    def test_bucket_index_various_distances(self):
        """Test bucket index calculation for various XOR distances."""
        table = RoutingTable(b'\x00' * 20)

        # Test a few different patterns
        # Second bit different: 01000000...
        target1 = b'\x40' + b'\x00' * 19
        self.assertEqual(table.get_bucket_index(target1), 158)

        # Third bit different: 00100000...
        target2 = b'\x20' + b'\x00' * 19
        self.assertEqual(table.get_bucket_index(target2), 157)

    def test_bucket_index_invalid_length(self):
        """Test that invalid target_id length raises ValueError."""
        table = RoutingTable(b'A' * 20)

        with self.assertRaises(ValueError) as ctx:
            table.get_bucket_index(b'short')
        self.assertIn("20 bytes", str(ctx.exception))

    def test_bucket_index_invalid_type(self):
        """Test that invalid target_id type raises TypeError."""
        table = RoutingTable(b'A' * 20)

        with self.assertRaises(TypeError) as ctx:
            table.get_bucket_index('not bytes')
        self.assertIn("target_id must be bytes", str(ctx.exception))

    def test_bucket_index_self(self):
        """Test that getting bucket for self raises ValueError."""
        node_id = b'A' * 20
        table = RoutingTable(node_id)

        with self.assertRaises(ValueError) as ctx:
            table.get_bucket_index(node_id)
        self.assertIn("own node_id", str(ctx.exception))


class TestAddNode(unittest.TestCase):
    """Test cases for adding nodes to routing table."""

    def test_add_node_success(self):
        """Test successfully adding a node."""
        table = RoutingTable(b'A' * 20)
        node = Node(b'B' * 20, '192.168.1.1', 6881)

        result = table.add_node(node)

        self.assertTrue(result)

    def test_add_node_duplicate(self):
        """Test adding the same node twice."""
        table = RoutingTable(b'A' * 20)
        node = Node(b'B' * 20, '192.168.1.1', 6881)

        # First add succeeds
        self.assertTrue(table.add_node(node))

        # Second add returns False (already exists)
        self.assertFalse(table.add_node(node))

    def test_add_node_bucket_placement(self):
        """Test that nodes are added to correct bucket."""
        table = RoutingTable(b'\x00' * 20, k=8)

        # Create node with only last bit different (should go to bucket 0)
        node = Node(b'\x00' * 19 + b'\x01', '192.168.1.1', 6881)
        table.add_node(node)

        # Check it's in bucket 0
        bucket_index = table.get_bucket_index(node.node_id)
        self.assertEqual(bucket_index, 0)
        self.assertIn(node, table.buckets[0])

    def test_add_node_bucket_full(self):
        """Test behavior when bucket is full."""
        table = RoutingTable(b'\x00' * 20, k=2)  # Small K for testing

        # Add nodes to same bucket (nodes with XOR distances 2 and 3 both go to bucket 1)
        # XOR 2 = 0b10, XOR 3 = 0b11 - both have bit_length=2, so bucket index = 1
        node1 = Node(b'\x00' * 19 + b'\x02', '192.168.1.1', 6881)  # bucket 1
        node2 = Node(b'\x00' * 19 + b'\x03', '192.168.1.2', 6881)  # bucket 1
        node3 = Node(b'\x00' * 19 + b'\x06', '192.168.1.3', 6881)  # bucket 2, but 0b110 & 0b010 XOR => bucket 2

        # Actually, let me use nodes that definitely go to the same bucket
        # For bucket 0: XOR must be 1 (only one value)
        # For bucket 1: XOR must be 2 or 3 (0b10 or 0b11)
        # All values from 2-3 go to bucket 1
        node1 = Node(b'\x00' * 19 + b'\x02', '192.168.1.1', 6881)  # XOR=2, bucket 1
        node2 = Node(b'\x00' * 19 + b'\x03', '192.168.1.2', 6881)  # XOR=3, bucket 1

        # First two should succeed
        self.assertTrue(table.add_node(node1))
        self.assertTrue(table.add_node(node2))

        # Bucket 1 should be full now, verify both nodes have same bucket
        bucket_index1 = table.get_bucket_index(node1.node_id)
        bucket_index2 = table.get_bucket_index(node2.node_id)
        self.assertEqual(bucket_index1, bucket_index2)
        self.assertEqual(len(table.buckets[bucket_index1]), 2)

        # Create a third node that goes to same bucket
        # We need another ID where XOR distance is 2 or 3
        # But we already used \x02 and \x03, and those are the only two
        # Let's use bucket 2 instead (XOR 4-7)
        table2 = RoutingTable(b'\x00' * 20, k=2)
        node_a = Node(b'\x00' * 19 + b'\x04', '192.168.1.1', 6881)  # XOR=4, bucket 2
        node_b = Node(b'\x00' * 19 + b'\x05', '192.168.1.2', 6881)  # XOR=5, bucket 2
        node_c = Node(b'\x00' * 19 + b'\x06', '192.168.1.3', 6881)  # XOR=6, bucket 2

        self.assertTrue(table2.add_node(node_a))
        self.assertTrue(table2.add_node(node_b))
        # Third should fail (bucket full)
        self.assertFalse(table2.add_node(node_c))

    def test_add_node_self(self):
        """Test that adding self raises ValueError."""
        node_id = b'A' * 20
        table = RoutingTable(node_id)
        node = Node(node_id, '192.168.1.1', 6881)

        with self.assertRaises(ValueError) as ctx:
            table.add_node(node)
        self.assertIn("own node", str(ctx.exception).lower())

    def test_add_node_invalid_type(self):
        """Test that adding non-Node object raises TypeError."""
        table = RoutingTable(b'A' * 20)

        with self.assertRaises(TypeError) as ctx:
            table.add_node("not a node")
        self.assertIn("Node object", str(ctx.exception))

    def test_add_multiple_nodes(self):
        """Test adding multiple nodes to different buckets."""
        table = RoutingTable(b'\x00' * 20, k=8)

        # Create nodes with different distances
        nodes = [
            Node(b'\x01' + b'\x00' * 19, '192.168.1.1', 6881),  # Far
            Node(b'\x00' * 19 + b'\x01', '192.168.1.2', 6881),  # Close
            Node(b'\x80' + b'\x00' * 19, '192.168.1.3', 6881),  # Very far
        ]

        for node in nodes:
            result = table.add_node(node)
            self.assertTrue(result)

        # Verify nodes are in different buckets
        bucket_indices = [table.get_bucket_index(node.node_id) for node in nodes]
        self.assertEqual(len(set(bucket_indices)), 3)  # All in different buckets


class TestRemoveNode(unittest.TestCase):
    """Test cases for removing nodes from routing table."""

    def test_remove_node_success(self):
        """Test successfully removing a node."""
        table = RoutingTable(b'A' * 20)
        node = Node(b'B' * 20, '192.168.1.1', 6881)

        table.add_node(node)
        result = table.remove_node(node)

        self.assertTrue(result)

    def test_remove_node_not_present(self):
        """Test removing a node that's not in the table."""
        table = RoutingTable(b'A' * 20)
        node = Node(b'B' * 20, '192.168.1.1', 6881)

        result = table.remove_node(node)

        self.assertFalse(result)

    def test_remove_node_twice(self):
        """Test removing the same node twice."""
        table = RoutingTable(b'A' * 20)
        node = Node(b'B' * 20, '192.168.1.1', 6881)

        table.add_node(node)

        # First removal succeeds
        self.assertTrue(table.remove_node(node))

        # Second removal fails
        self.assertFalse(table.remove_node(node))

    def test_remove_node_invalid_type(self):
        """Test that removing non-Node object raises TypeError."""
        table = RoutingTable(b'A' * 20)

        with self.assertRaises(TypeError) as ctx:
            table.remove_node("not a node")
        self.assertIn("Node object", str(ctx.exception))

    def test_remove_node_from_bucket(self):
        """Test that node is actually removed from bucket."""
        table = RoutingTable(b'\x00' * 20)
        node = Node(b'\x00' * 19 + b'\x01', '192.168.1.1', 6881)

        table.add_node(node)
        bucket_index = table.get_bucket_index(node.node_id)

        # Verify node is in bucket
        self.assertIn(node, table.buckets[bucket_index])

        # Remove node
        table.remove_node(node)

        # Verify node is no longer in bucket
        self.assertNotIn(node, table.buckets[bucket_index])


class TestGetClosestNodes(unittest.TestCase):
    """Test cases for finding closest nodes."""

    def test_get_closest_empty_table(self):
        """Test getting closest nodes from empty table."""
        table = RoutingTable(b'A' * 20)
        target = b'B' * 20

        closest = table.get_closest_nodes(target)

        self.assertEqual(len(closest), 0)

    def test_get_closest_single_node(self):
        """Test getting closest nodes with only one node in table."""
        table = RoutingTable(b'A' * 20)
        node = Node(b'B' * 20, '192.168.1.1', 6881)

        table.add_node(node)
        closest = table.get_closest_nodes(b'C' * 20)

        self.assertEqual(len(closest), 1)
        self.assertEqual(closest[0], node)

    def test_get_closest_multiple_nodes(self):
        """Test getting closest nodes with multiple nodes."""
        table = RoutingTable(b'\x00' * 20, k=20)

        # Add several nodes
        nodes = [
            Node(b'\x01' + b'\x00' * 19, '192.168.1.1', 6881),
            Node(b'\x02' + b'\x00' * 19, '192.168.1.2', 6881),
            Node(b'\x03' + b'\x00' * 19, '192.168.1.3', 6881),
            Node(b'\x04' + b'\x00' * 19, '192.168.1.4', 6881),
        ]

        for node in nodes:
            table.add_node(node)

        # Target closer to first node
        target = b'\x01' + b'\x00' * 19
        closest = table.get_closest_nodes(target, count=2)

        self.assertEqual(len(closest), 2)
        # First result should be the closest (node with ID \x01...)
        self.assertEqual(closest[0].node_id, b'\x01' + b'\x00' * 19)

    def test_get_closest_sorted_by_distance(self):
        """Test that returned nodes are sorted by distance."""
        table = RoutingTable(b'\x00' * 20, k=20)

        # Add nodes with known distances
        nodes = [
            Node(b'\x10' + b'\x00' * 19, '192.168.1.1', 6881),
            Node(b'\x01' + b'\x00' * 19, '192.168.1.2', 6881),
            Node(b'\x08' + b'\x00' * 19, '192.168.1.3', 6881),
        ]

        for node in nodes:
            table.add_node(node)

        # Get all nodes
        target = b'\x00' * 20
        closest = table.get_closest_nodes(target, count=10)

        # Verify they're sorted by distance
        from node import distance
        for i in range(len(closest) - 1):
            dist1 = distance(closest[i].node_id, target)
            dist2 = distance(closest[i + 1].node_id, target)
            self.assertLessEqual(dist1, dist2)

    def test_get_closest_limited_count(self):
        """Test that count parameter limits results."""
        table = RoutingTable(b'\x00' * 20, k=20)

        # Add 10 nodes
        for i in range(10):
            node_id = bytes([i + 1]) + b'\x00' * 19
            node = Node(node_id, f'192.168.1.{i}', 6881)
            table.add_node(node)

        # Request only 3
        closest = table.get_closest_nodes(b'\x05' + b'\x00' * 19, count=3)

        self.assertEqual(len(closest), 3)

    def test_get_closest_invalid_target_length(self):
        """Test that invalid target_id length raises ValueError."""
        table = RoutingTable(b'A' * 20)

        with self.assertRaises(ValueError) as ctx:
            table.get_closest_nodes(b'short')
        self.assertIn("20 bytes", str(ctx.exception))

    def test_get_closest_invalid_target_type(self):
        """Test that invalid target_id type raises TypeError."""
        table = RoutingTable(b'A' * 20)

        with self.assertRaises(TypeError) as ctx:
            table.get_closest_nodes('not bytes')
        self.assertIn("target_id must be bytes", str(ctx.exception))

    def test_get_closest_invalid_count(self):
        """Test that invalid count raises ValueError."""
        table = RoutingTable(b'A' * 20)
        target = b'B' * 20

        # Zero count
        with self.assertRaises(ValueError) as ctx:
            table.get_closest_nodes(target, count=0)
        self.assertIn("positive", str(ctx.exception))

        # Negative count
        with self.assertRaises(ValueError):
            table.get_closest_nodes(target, count=-1)

        # Too large count
        with self.assertRaises(ValueError) as ctx:
            table.get_closest_nodes(target, count=1001)
        self.assertIn("too large", str(ctx.exception))

    def test_get_closest_invalid_count_type(self):
        """Test that invalid count type raises TypeError."""
        table = RoutingTable(b'A' * 20)
        target = b'B' * 20

        with self.assertRaises(TypeError) as ctx:
            table.get_closest_nodes(target, count='8')
        self.assertIn("count must be int", str(ctx.exception))


if __name__ == '__main__':
    # Run tests with verbose output
    unittest.main(verbosity=2)
