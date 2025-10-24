#!/usr/bin/env python3
"""
BitTorrent DHT Scraper - Command Line Interface

This script connects to the real BitTorrent DHT network and scrapes
peers for a given torrent info_hash.

Usage:
    python scraper.py <info_hash>
    python scraper.py --help

Examples:
    # Scrape peers for a torrent (hex format)
    python scraper.py 0123456789abcdef0123456789abcdef01234567

    # Scrape with longer timeout
    python scraper.py 0123456789abcdef0123456789abcdef01234567 --timeout 30
"""

import sys
import os
import argparse
import time

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from dht_client import DHTClient
from progress_display import (
    format_elapsed_time,
    calculate_rate,
    format_progress_line,
    clear_progress_line
)


def parse_info_hash(hash_str: str) -> bytes:
    """
    Parse info hash from hex string.

    Args:
        hash_str: 40-character hex string

    Returns:
        bytes: 20-byte info hash

    Raises:
        ValueError: If hash format is invalid
    """
    # Remove any whitespace
    hash_str = hash_str.strip()

    # Check if it's hex format (40 chars)
    if len(hash_str) == 40:
        try:
            return bytes.fromhex(hash_str)
        except ValueError:
            raise ValueError(f"Invalid hex string: {hash_str}")

    # Check if it's already 20 bytes (unlikely from CLI)
    if len(hash_str) == 20:
        return hash_str.encode('latin-1')

    raise ValueError(f"Info hash must be 40-character hex string, got {len(hash_str)} characters")


def format_peers(peers):
    """Format peer list for display."""
    if not peers:
        return "No peers found"

    lines = [f"\nFound {len(peers)} peer(s):"]
    lines.append("-" * 50)

    for i, (ip, port) in enumerate(peers[:50], 1):  # Limit display to 50
        lines.append(f"{i:3d}. {ip:15s}:{port}")

    if len(peers) > 50:
        lines.append(f"... and {len(peers) - 50} more")

    return "\n".join(lines)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='BitTorrent DHT Scraper - Find peers for a torrent',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # CRAWLER MODE: Discover info_hashes being shared on DHT
  %(prog)s                    # 15 second crawl
  %(prog)s --timeout 60       # 60 second crawl
  %(prog)s --timeout 0        # INFINITE crawl (Ctrl+C to stop)

  # SCRAPER MODE: Find peers for specific torrent
  %(prog)s 0123456789abcdef0123456789abcdef01234567
  %(prog)s 0123456789abcdef0123456789abcdef01234567 --timeout 30

  # Advanced options
  %(prog)s --port 6881
  %(prog)s --bootstrap router.bittorrent.com:6881

Note: Use --timeout 0 for infinite crawling. Press Ctrl+C to stop.
        """
    )

    parser.add_argument(
        'info_hash',
        nargs='?',  # Make it optional
        help='Torrent info_hash as 40-character hex string (omit to crawl DHT)'
    )

    parser.add_argument(
        '--timeout',
        type=float,
        default=15.0,
        help='Search timeout in seconds (default: 15, use 0 for infinite)'
    )

    parser.add_argument(
        '--port',
        type=int,
        default=0,
        help='UDP port to bind to (default: random)'
    )

    parser.add_argument(
        '--bootstrap',
        nargs='+',
        help='Custom bootstrap nodes (format: host:port)'
    )

    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Verbose output'
    )

    args = parser.parse_args()

    # Check if running in crawler mode (no info_hash provided)
    crawler_mode = args.info_hash is None

    if not crawler_mode:
        # Parse info hash
        try:
            info_hash = parse_info_hash(args.info_hash)
        except ValueError as e:
            print(f"Error: {e}", file=sys.stderr)
            return 1

    print("=" * 60)
    if crawler_mode:
        print("BitTorrent DHT Network Crawler")
    else:
        print("BitTorrent DHT Peer Scraper")
    print("=" * 60)

    if not crawler_mode:
        print(f"\nInfo Hash: {info_hash.hex()}")
        timeout_str = "infinite" if args.timeout == 0 else f"{args.timeout}s"
        print(f"Timeout:   {timeout_str}")
    else:
        print(f"\nMode:      CRAWLER (discovering info_hashes)")
        if args.timeout == 0:
            print(f"Duration:  INFINITE (press Ctrl+C to stop)")
        else:
            print(f"Duration:  {args.timeout}s (press Ctrl+C to stop early)")
    print()

    # Create DHT client
    try:
        client = DHTClient(port=args.port)
        client.start()
    except Exception as e:
        print(f"Error starting DHT client: {e}", file=sys.stderr)
        return 1

    try:
        # Parse custom bootstrap nodes if provided
        bootstrap_nodes = None
        if args.bootstrap:
            bootstrap_nodes = []
            for node_str in args.bootstrap:
                try:
                    host, port = node_str.rsplit(':', 1)
                    bootstrap_nodes.append((host, int(port)))
                except ValueError:
                    print(f"Warning: Invalid bootstrap node format: {node_str}")

        # Bootstrap
        print("[1/3] Bootstrapping DHT...")
        success = client.bootstrap(bootstrap_nodes)

        if not success:
            print("\nError: Bootstrap failed. Unable to connect to DHT network.")
            print("This could be due to:")
            print("  - Network connectivity issues")
            print("  - Firewall blocking UDP traffic")
            print("  - DHT bootstrap nodes being unavailable")
            return 1

        # Brief pause to let routing table populate
        time.sleep(1.0)

        # Check routing table
        total_nodes = sum(len(bucket) for bucket in client.routing_table.buckets)
        print(f"✓ Routing table populated with {total_nodes} nodes")

        if crawler_mode:
            # CRAWLER MODE - Discover info_hashes
            infinite_mode = args.timeout == 0

            if infinite_mode:
                print(f"\n[2/3] Crawling DHT network (INFINITE MODE)...")
                print("Listening for get_peers queries to discover info_hashes...")
                print("Press Ctrl+C to stop\n")
            else:
                print(f"\n[2/3] Crawling DHT network (duration: {args.timeout}s)...")
                print("Listening for get_peers queries to discover info_hashes...")
                print("Press Ctrl+C to stop early\n")

            discovered_count = 0
            total_requests = 0
            last_progress_update = 0.0
            progress_update_interval = 1.0  # Update progress every 1 second

            def on_discovery(info_hash, addr):
                nonlocal discovered_count, total_requests, last_progress_update
                total_requests += 1

                # Check if this is a new unique info_hash
                is_new = info_hash not in client.discovered_info_hashes or \
                         len(client.discovered_info_hashes[info_hash].get('sources', [])) == 1

                if is_new:
                    discovered_count += 1
                    print(f"[{discovered_count:4d}] {info_hash.hex()}  (from {addr[0]})")

                # Update progress line for INFINITE mode
                if infinite_mode:
                    current_time = time.time()
                    if current_time - last_progress_update >= progress_update_interval:
                        elapsed = current_time - start_time
                        rate = calculate_rate(discovered_count, elapsed)
                        table_size = sum(len(bucket) for bucket in client.routing_table.buckets)

                        # Clear previous progress line and print new one
                        progress = format_progress_line(
                            elapsed=elapsed,
                            count=discovered_count,
                            rate=rate,
                            total_requests=total_requests,
                            table_size=table_size
                        )
                        print(clear_progress_line() + progress, end='', flush=True)
                        last_progress_update = current_time

            start_time = time.time()

            try:
                results = client.crawl_network(duration=args.timeout, callback=on_discovery)
                # Clear the progress line before showing final results
                if infinite_mode:
                    print()  # New line after progress
            except KeyboardInterrupt:
                # Clear the progress line before showing stop message
                if infinite_mode:
                    print()  # New line after progress
                print("\n\nStopping crawler...")
                results = dict(client.discovered_info_hashes)

            elapsed = time.time() - start_time

            # Display results
            print(f"\n[3/3] Results:")
            print("=" * 60)
            print(f"Crawl completed in {elapsed:.1f}s")
            print(f"Discovered {len(results)} unique info_hash(es)")
            print("=" * 60)

            if results:
                print("\nTop info_hashes by peer request count:")
                print("-" * 60)

                # Sort by peer count
                sorted_hashes = sorted(
                    results.items(),
                    key=lambda x: x[1]['peer_count'],
                    reverse=True
                )

                for i, (info_hash, data) in enumerate(sorted_hashes[:20], 1):
                    count = data['peer_count']
                    sources = len(data['sources'])
                    print(f"{i:3d}. {info_hash.hex()}  ({count} requests, {sources} sources)")

                if len(results) > 20:
                    print(f"\n... and {len(results) - 20} more")

                print("\n" + "=" * 60)
                print("SUCCESS: Info hashes discovered!")
                print("=" * 60)
                print("\nYou can now scrape peers for any of these:")
                print(f"  ./scraper.py {sorted_hashes[0][0].hex()}")
            else:
                print("\nNo info_hashes discovered.")
                print("The network may be quiet, or try increasing duration.")

            return 0

        else:
            # REGULAR MODE - Find peers for specific info_hash
            print(f"\n[2/3] Searching DHT for peers (timeout: {args.timeout}s)...")
            print("This may take a while...")

            start_time = time.time()
            peers = client.get_peers(info_hash, timeout=args.timeout)
            elapsed = time.time() - start_time

            print(f"✓ Search completed in {elapsed:.1f}s")

            # Display results
            print(f"\n[3/3] Results:")
            print(format_peers(peers))

            if peers:
                print("\n" + "=" * 60)
                print("SUCCESS: Peers found!")
                print("=" * 60)
                return 0
            else:
                print("\n" + "=" * 60)
                print("No peers found for this info_hash")
                print("=" * 60)
                print("\nPossible reasons:")
                print("  - Info hash may be invalid or very rare")
                print("  - Torrent may have no active peers")
                print("  - Try increasing --timeout")
                return 0

    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
        return 130

    except Exception as e:
        print(f"\nError: {e}", file=sys.stderr)
        import traceback
        if args.verbose:
            traceback.print_exc()
        return 1

    finally:
        client.stop()


if __name__ == '__main__':
    sys.exit(main())
