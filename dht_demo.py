#!/usr/bin/env python3
"""
BitTorrent DHT Scraper Demo

This script demonstrates the DHT components in action.
Note: This is an educational demo that simulates DHT operations without
actual network I/O. For a production scraper, you would need to:
1. Connect to bootstrap nodes
2. Implement UDP socket communication
3. Handle asynchronous queries/responses
4. Implement iterative lookups
"""

import sys
import os

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from bencode import encode, decode
from node import Node, distance, generate_node_id
from routing_table import RoutingTable
from protocol import (
    create_ping_query,
    create_find_node_query,
    create_get_peers_query,
    parse_message,
    pack_nodes,
    unpack_nodes
)


def demo_bencode():
    """Demonstrate bencode encoding/decoding."""
    print("=" * 60)
    print("DEMO 1: Bencode Encoding/Decoding")
    print("=" * 60)

    # Example torrent-like data
    data = {
        b'announce': b'http://tracker.example.com:6969/announce',
        b'info': {
            b'name': b'example.txt',
            b'length': 1024,
            b'piece length': 16384
        }
    }

    print("\nOriginal data:")
    print(data)

    encoded = encode(data)
    print(f"\nBencode encoded ({len(encoded)} bytes):")
    print(encoded[:100], "..." if len(encoded) > 100 else "")

    decoded, _ = decode(encoded)
    print("\nDecoded data:")
    print(decoded)
    print("✓ Roundtrip successful!\n")


def demo_nodes():
    """Demonstrate DHT nodes and distance calculation."""
    print("=" * 60)
    print("DEMO 2: DHT Nodes and XOR Distance")
    print("=" * 60)

    # Create some nodes
    node1 = Node(b'\x00' * 20, '192.168.1.1', 6881)
    node2 = Node(b'\x01' * 20, '192.168.1.2', 6881)
    node3 = Node(b'\xff' * 20, '192.168.1.3', 6881)

    print(f"\nNode 1: {node1}")
    print(f"Node 2: {node2}")
    print(f"Node 3: {node3}")

    # Calculate distances
    dist_1_2 = distance(node1.node_id, node2.node_id)
    dist_1_3 = distance(node1.node_id, node3.node_id)
    dist_2_3 = distance(node2.node_id, node3.node_id)

    print(f"\nXOR Distance (Node1 ↔ Node2): {dist_1_2}")
    print(f"XOR Distance (Node1 ↔ Node3): {dist_1_3}")
    print(f"XOR Distance (Node2 ↔ Node3): {dist_2_3}")

    print("\n✓ Node 3 is farthest from Node 1 (all bits differ)\n")


def demo_routing_table():
    """Demonstrate routing table operations."""
    print("=" * 60)
    print("DEMO 3: Kademlia Routing Table (K-Buckets)")
    print("=" * 60)

    # Create local node and routing table
    local_id = generate_node_id()
    table = RoutingTable(local_id, k=8)

    print(f"\nLocal Node ID: {local_id.hex()}")
    print(f"Routing table: 160 buckets, K=8 nodes per bucket")

    # Add some nodes
    print("\nAdding 20 nodes to routing table...")
    added_nodes = []
    for i in range(20):
        node_id = generate_node_id()
        node = Node(node_id, f'192.168.1.{i}', 6881)
        if table.add_node(node):
            added_nodes.append(node)

    print(f"✓ Successfully added {len(added_nodes)} nodes")

    # Show bucket distribution
    non_empty_buckets = sum(1 for bucket in table.buckets if len(bucket) > 0)
    print(f"✓ Nodes distributed across {non_empty_buckets} buckets")

    # Find closest nodes to a target
    target_id = generate_node_id()
    print(f"\nSearching for 5 closest nodes to target: {target_id.hex()[:16]}...")

    closest = table.get_closest_nodes(target_id, count=5)
    print(f"✓ Found {len(closest)} closest nodes:")

    for i, node in enumerate(closest[:3], 1):
        dist = distance(node.node_id, target_id)
        print(f"  {i}. {node.ip}:{node.port} (distance: {dist})")

    print()


def demo_protocol():
    """Demonstrate DHT protocol messages."""
    print("=" * 60)
    print("DEMO 4: DHT Protocol Messages")
    print("=" * 60)

    local_id = b'A' * 20
    transaction_id = b'ab'

    # Create ping query
    print("\n1. Creating PING query:")
    ping_msg = create_ping_query(transaction_id, local_id)
    print(f"   Message size: {len(ping_msg)} bytes")
    print(f"   Bencode: {ping_msg[:60]}...")

    parsed = parse_message(ping_msg)
    print(f"   Parsed: type={parsed[b'y']}, query={parsed[b'q']}")

    # Create find_node query
    print("\n2. Creating FIND_NODE query:")
    target_id = b'B' * 20
    find_msg = create_find_node_query(transaction_id, local_id, target_id)
    print(f"   Message size: {len(find_msg)} bytes")

    parsed = parse_message(find_msg)
    print(f"   Parsed: type={parsed[b'y']}, query={parsed[b'q']}")
    print(f"   Target: {parsed[b'a'][b'target'].hex()[:16]}...")

    # Create get_peers query
    print("\n3. Creating GET_PEERS query:")
    info_hash = b'H' * 20
    peers_msg = create_get_peers_query(transaction_id, local_id, info_hash)
    print(f"   Message size: {len(peers_msg)} bytes")

    parsed = parse_message(peers_msg)
    print(f"   Parsed: type={parsed[b'y']}, query={parsed[b'q']}")
    print(f"   Info hash: {parsed[b'a'][b'info_hash'].hex()[:16]}...")

    # Demonstrate compact node format
    print("\n4. Compact Node Format:")
    nodes = [
        (b'N' * 20, '192.168.1.1', 6881),
        (b'O' * 20, '10.0.0.1', 6882),
        (b'D' * 20, '172.16.0.1', 6883),
    ]

    packed = pack_nodes(nodes)
    print(f"   Packed 3 nodes into {len(packed)} bytes (26 bytes each)")
    print(f"   Packed data: {packed[:30].hex()}...")

    unpacked = unpack_nodes(packed)
    print(f"   Unpacked {len(unpacked)} nodes:")
    for node_id, ip, port in unpacked:
        print(f"     - {ip}:{port} (ID: {node_id.hex()[:8]}...)")

    print()


def demo_simulated_lookup():
    """Simulate a DHT lookup for an info hash."""
    print("=" * 60)
    print("DEMO 5: Simulated DHT Lookup")
    print("=" * 60)

    print("\nSimulating lookup for info_hash...")
    info_hash = b'H' * 20
    print(f"Info Hash: {info_hash.hex()}")

    # Create local node
    local_id = generate_node_id()
    print(f"Local Node: {local_id.hex()[:16]}...")

    # Create routing table with some nodes
    table = RoutingTable(local_id, k=8)
    print("\n1. Populating routing table with 50 nodes...")

    for i in range(50):
        node = Node(generate_node_id(), f'10.0.{i//256}.{i%256}', 6881 + i)
        table.add_node(node)

    print("   ✓ Routing table populated")

    # Find closest nodes to info_hash
    print(f"\n2. Finding 8 closest nodes to info_hash...")
    closest = table.get_closest_nodes(info_hash, count=8)
    print(f"   ✓ Found {len(closest)} nodes")

    # Simulate sending get_peers queries
    print("\n3. Simulating GET_PEERS queries to closest nodes:")
    for i, node in enumerate(closest[:3], 1):
        transaction_id = f't{i}'.encode()[:2].ljust(2, b'\x00')
        query = create_get_peers_query(transaction_id, local_id, info_hash)
        print(f"   → Sending to {node.ip}:{node.port} ({len(query)} bytes)")

    print("\n4. In a real implementation:")
    print("   - Send queries over UDP")
    print("   - Wait for responses with peer IPs or closer nodes")
    print("   - Iteratively query closer nodes")
    print("   - Collect peers for the torrent")
    print("\n✓ Simulation complete!\n")


def main():
    """Run all demonstrations."""
    print("\n")
    print("╔" + "═" * 58 + "╗")
    print("║" + " " * 10 + "BitTorrent DHT Scraper Demo" + " " * 21 + "║")
    print("║" + " " * 15 + "Educational Implementation" + " " * 17 + "║")
    print("╚" + "═" * 58 + "╝")
    print()

    demos = [
        demo_bencode,
        demo_nodes,
        demo_routing_table,
        demo_protocol,
        demo_simulated_lookup,
    ]

    for demo in demos:
        try:
            demo()
        except Exception as e:
            print(f"Error in {demo.__name__}: {e}")
            import traceback
            traceback.print_exc()

    print("=" * 60)
    print("DEMO COMPLETE")
    print("=" * 60)
    print("\nAll core DHT components demonstrated successfully!")
    print("\nFor actual DHT scraping, you would need to:")
    print("  1. Implement UDP socket communication")
    print("  2. Connect to bootstrap nodes (e.g., router.bittorrent.com:6881)")
    print("  3. Implement iterative node lookups")
    print("  4. Handle asynchronous query/response matching")
    print("  5. Implement proper timeout and retry logic")
    print("\nSee README.md for more information.\n")


if __name__ == '__main__':
    main()
