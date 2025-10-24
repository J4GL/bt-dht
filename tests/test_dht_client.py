"""
Unit tests for DHT Client module.

This test suite validates the DHT client initialization and basic functions.
Network I/O is tested separately.
"""

import unittest
import sys
import os

# Add src directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from dht_client import DHTClient


class TestDHTClientInit(unittest.TestCase):
    """Test cases for DHT client initialization."""

    def test_init_defaults(self):
        """Test creating client with default parameters."""
        client = DHTClient()

        self.assertIsNotNone(client.node_id)
        self.assertEqual(len(client.node_id), 20)
        self.assertEqual(client.port, 0)
        self.assertIsNotNone(client.routing_table)
        self.assertFalse(client.running)

    def test_init_custom_port(self):
        """Test creating client with custom port."""
        client = DHTClient(port=6881)

        self.assertEqual(client.port, 6881)

    def test_init_custom_node_id(self):
        """Test creating client with custom node ID."""
        node_id = b'A' * 20
        client = DHTClient(node_id=node_id)

        self.assertEqual(client.node_id, node_id)

    def test_init_invalid_port_type(self):
        """Test that invalid port type raises TypeError."""
        with self.assertRaises(TypeError) as ctx:
            DHTClient(port='6881')
        self.assertIn("port must be int", str(ctx.exception))

    def test_init_invalid_port_range(self):
        """Test that invalid port range raises ValueError."""
        # Negative port
        with self.assertRaises(ValueError) as ctx:
            DHTClient(port=-1)
        self.assertIn("0-65535", str(ctx.exception))

        # Port too high
        with self.assertRaises(ValueError):
            DHTClient(port=65536)

    def test_init_invalid_node_id_length(self):
        """Test that invalid node_id length raises ValueError."""
        with self.assertRaises(ValueError) as ctx:
            DHTClient(node_id=b'short')
        self.assertIn("20 bytes", str(ctx.exception))

    def test_init_invalid_node_id_type(self):
        """Test that invalid node_id type raises ValueError."""
        with self.assertRaises(ValueError):
            DHTClient(node_id='not bytes')

    def test_routing_table_created(self):
        """Test that routing table is properly initialized."""
        node_id = b'B' * 20
        client = DHTClient(node_id=node_id)

        self.assertEqual(client.routing_table.node_id, node_id)
        self.assertEqual(client.routing_table.k, 8)

    def test_pending_queries_empty(self):
        """Test that pending queries starts empty."""
        client = DHTClient()

        self.assertEqual(len(client.pending_queries), 0)
        self.assertIsInstance(client.pending_queries, dict)

    def test_transaction_counter_starts_at_zero(self):
        """Test transaction counter initialization."""
        client = DHTClient()

        self.assertEqual(client.transaction_counter, 0)


class TestDHTClientTransactionID(unittest.TestCase):
    """Test cases for transaction ID generation."""

    def test_get_transaction_id_format(self):
        """Test that transaction IDs are 2 bytes."""
        client = DHTClient()

        tid = client._get_transaction_id()

        self.assertIsInstance(tid, bytes)
        self.assertEqual(len(tid), 2)

    def test_get_transaction_id_increments(self):
        """Test that transaction IDs increment."""
        client = DHTClient()

        tid1 = client._get_transaction_id()
        tid2 = client._get_transaction_id()
        tid3 = client._get_transaction_id()

        # Should be sequential
        self.assertEqual(int.from_bytes(tid1, 'big'), 1)
        self.assertEqual(int.from_bytes(tid2, 'big'), 2)
        self.assertEqual(int.from_bytes(tid3, 'big'), 3)

    def test_get_transaction_id_unique(self):
        """Test that transaction IDs are unique."""
        client = DHTClient()

        tids = [client._get_transaction_id() for _ in range(100)]

        # All should be unique
        self.assertEqual(len(set(tids)), 100)


class TestDHTClientValidation(unittest.TestCase):
    """Test cases for input validation in client methods."""

    def test_get_peers_invalid_info_hash_length(self):
        """Test that invalid info_hash length raises ValueError."""
        client = DHTClient()

        with self.assertRaises(ValueError) as ctx:
            client.get_peers(b'short')
        self.assertIn("20 bytes", str(ctx.exception))

    def test_get_peers_invalid_info_hash_type(self):
        """Test that invalid info_hash type raises ValueError."""
        client = DHTClient()

        with self.assertRaises(ValueError):
            client.get_peers('not bytes')

    def test_find_node_invalid_target_id_length(self):
        """Test that invalid target_id length raises ValueError."""
        client = DHTClient()

        with self.assertRaises(ValueError) as ctx:
            client.find_node(b'short')
        self.assertIn("20 bytes", str(ctx.exception))

    def test_find_node_invalid_target_id_type(self):
        """Test that invalid target_id type raises ValueError."""
        client = DHTClient()

        with self.assertRaises(ValueError):
            client.find_node('not bytes')


class TestDHTClientState(unittest.TestCase):
    """Test cases for client state management."""

    def test_initial_state_not_running(self):
        """Test that client starts in not running state."""
        client = DHTClient()

        self.assertFalse(client.running)
        self.assertIsNone(client.socket)
        self.assertIsNone(client.receive_thread)

    def test_stop_when_not_running(self):
        """Test that stopping non-running client doesn't error."""
        client = DHTClient()

        # Should not raise exception
        client.stop()

        self.assertFalse(client.running)


if __name__ == '__main__':
    # Run tests with verbose output
    unittest.main(verbosity=2)
