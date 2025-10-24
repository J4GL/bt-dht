# BitTorrent DHT Scraper

An educational implementation of a BitTorrent DHT (Distributed Hash Table) scraper in Python using only the standard library. This project demonstrates the Kademlia DHT protocol used by BitTorrent for distributed peer discovery.

## Overview

This project implements the core components of the BitTorrent DHT protocol (BEP 5) from scratch without external dependencies. It includes:

- **Bencode encoding/decoding**: The data serialization format used by BitTorrent
- **DHT Node representation**: Managing node identities and XOR distance metrics
- **Kademlia Routing Table**: K-bucket based routing for efficient lookups
- **DHT Protocol Messages**: Creating and parsing ping, find_node, and get_peers queries

## Project Structure

```
bt-dht/
├── src/
│   ├── bencode.py          # Bencode encoding/decoding (BEP 3)
│   ├── node.py             # DHT Node class and distance calculations
│   ├── routing_table.py    # Kademlia routing table (K-buckets)
│   └── protocol.py         # DHT protocol message handling (BEP 5)
├── tests/
│   ├── test_bencode.py     # 43 tests for bencode module
│   ├── test_node.py        # 35 tests for node module
│   ├── test_routing_table.py  # 34 tests for routing table
│   └── test_protocol.py    # 36 tests for protocol module
├── prompts/
│   └── 2025-10-24_bittorrent_dht_scraper.yaml
├── MEMORY/
│   ├── PLAN_2025-10-24_bittorrent_dht_scraper.md
│   └── SECURITY_REVIEW_2025-10-24_bittorrent_dht_scraper.md
└── README.md
```

## Features

### Bencode Module (`src/bencode.py`)
- Encode Python objects (int, bytes, list, dict) to bencode format
- Decode bencode data back to Python objects
- Full validation and error handling
- Support for nested structures

### Node Module (`src/node.py`)
- Node class representing DHT participants
- XOR distance calculation for Kademlia routing
- Cryptographically secure node ID generation
- IPv4 and IPv6 support

### Routing Table Module (`src/routing_table.py`)
- Kademlia K-bucket implementation
- 160 buckets for 160-bit ID space
- LRU eviction policy
- Efficient closest node lookups

### Protocol Module (`src/protocol.py`)
- DHT message creation (ping, find_node, get_peers)
- Message parsing with validation
- Compact node format packing/unpacking
- Full BEP 5 compliance for implemented features

## Installation & Usage

No external dependencies required! Uses only Python standard library.

```bash
# Clone or download the repository
cd bt-dht
```

### 🚀 Running the REAL DHT Scraper

The scraper has **TWO MODES**:

#### **Mode 1: CRAWLER - Discover info_hashes** (Run without arguments)

Discover what torrents are being shared on the DHT network:

```bash
# Make scraper executable
chmod +x scraper.py

# Run in crawler mode (no arguments!)
./scraper.py

# Crawl for longer to discover more
./scraper.py --timeout 120

# INFINITE CRAWL - Run until you stop it (Ctrl+C)
./scraper.py --timeout 0

# Adjust active query interval for more/less DHT visibility
./scraper.py --timeout 0 --query-interval 1   # Aggressive (max visibility)
./scraper.py --timeout 0 --query-interval 10  # Conservative (low traffic)
```

**What happens:**
- Joins the BitTorrent DHT as a node
- Listens for get_peers queries from other clients
- Discovers info_hashes as they're being searched
- Shows real-time discoveries + summary
- Progress updates every second (in INFINITE mode)

**Example output:**
```
[   1] 2d066c94480adcf5b7ab60065f24e681a57e011f  (from 91.201.41.182)
[   2] 8e4a3e30b8c96f9a7c0d2e1f3b4c5d6a7e8f9a0b  (from 176.31.107.216)
[   3] 1a2b3c4d5e6f7a8b9c0d1e2f3a4b5c6d7e8f9a0b  (from 85.214.132.117)
...

Discovered 47 unique info_hash(es)
Top info_hashes by request count:
  1. 2d066c94480adcf5b7ab60065f24e681a57e011f  (23 requests, 12 sources)
  2. 8e4a3e30b8c96f9a7c0d2e1f3b4c5d6a7e8f9a0b  (18 requests, 9 sources)
```

#### **Mode 2: SCRAPER - Find peers for torrent** (Provide info_hash)

Find peers sharing a specific torrent:

```bash
# Scrape peers for a torrent (using info_hash)
./scraper.py <40-char-hex-info-hash>

# Example: Ubuntu 20.04 Desktop
./scraper.py 2d066c94480adcf5b7ab60065f24e681a57e011f

# With longer timeout for better results
./scraper.py 2d066c94480adcf5b7ab60065f24e681a57e011f --timeout 30
```

**What happens:**
1. Connects to real BitTorrent DHT bootstrap nodes
2. Populates routing table with actual DHT nodes
3. Performs iterative lookups for the info_hash
4. Returns IP:port list of peers sharing the torrent

**Get help:**
```bash
./scraper.py --help
```

**Note:**
- Use `--timeout 0` for **infinite crawling** (great for long-term monitoring!)
- Press `Ctrl+C` to stop at any time
- Finding peers typically takes 10-60 seconds

### Running the Educational Demo

For learning purposes, run the demo that explains each component:

```bash
python dht_demo.py
```

This demonstrates:
1. **Bencode Encoding/Decoding** - BitTorrent's data format
2. **DHT Nodes and XOR Distance** - Kademlia distance metric
3. **Kademlia Routing Table** - K-bucket organization
4. **DHT Protocol Messages** - Creating and parsing queries
5. **Simulated DHT Lookup** - How lookups work (without network I/O)

### Running Tests

```bash
# Run all unit tests (194 total)
python tests/test_bencode.py        # 43 tests
python tests/test_node.py           # 35 tests
python tests/test_routing_table.py  # 34 tests
python tests/test_protocol.py       # 36 tests
python tests/test_dht_client.py     # 25 tests
python tests/test_progress_display.py  # 21 tests

# Run end-to-end tests (13 tests)
bash tests/test_e2e.sh
```

**Test Coverage:**
- **194 unit tests** - Test individual functions
- **13 end-to-end tests** - Test complete CLI workflows
- **Total: 207 tests** - All passing ✓

## Usage Examples

### Bencode Encoding/Decoding

```python
from src.bencode import encode, decode

# Encode data
data = {b'name': b'example', b'value': 42}
encoded = encode(data)
print(encoded)  # b'd4:name7:example5:valuei42ee'

# Decode data
decoded, consumed = decode(encoded)
print(decoded)  # {b'name': b'example', b'value': 42}
```

### Working with DHT Nodes

```python
from src.node import Node, distance, generate_node_id

# Create a node
node_id = generate_node_id()
node = Node(node_id, '192.168.1.1', 6881)

# Calculate XOR distance between nodes
node1_id = b'\x00' * 20
node2_id = b'\x01' * 20
dist = distance(node1_id, node2_id)
print(f"Distance: {dist}")
```

### Using the Routing Table

```python
from src.routing_table import RoutingTable
from src.node import Node, generate_node_id

# Create routing table
local_id = generate_node_id()
table = RoutingTable(local_id, k=8)

# Add nodes
node1 = Node(generate_node_id(), '192.168.1.1', 6881)
node2 = Node(generate_node_id(), '192.168.1.2', 6881)
table.add_node(node1)
table.add_node(node2)

# Find closest nodes to a target
target_id = generate_node_id()
closest = table.get_closest_nodes(target_id, count=8)
print(f"Found {len(closest)} closest nodes")
```

### Creating DHT Messages

```python
from src.protocol import create_ping_query, create_get_peers_query, parse_message

# Create a ping query
transaction_id = b'aa'
node_id = b'A' * 20
ping_msg = create_ping_query(transaction_id, node_id)

# Parse the message
parsed = parse_message(ping_msg)
print(parsed[b'q'])  # b'ping'

# Create get_peers query
info_hash = b'H' * 20
get_peers_msg = create_get_peers_query(transaction_id, node_id, info_hash)
```

## Testing

The project includes comprehensive unit tests with 148 total tests covering all modules:

```bash
# Run all tests
python tests/test_bencode.py       # 43 tests
python tests/test_node.py          # 35 tests
python tests/test_routing_table.py # 34 tests
python tests/test_protocol.py      # 36 tests
```

All tests validate both correct behavior (happy path) and error handling (edge cases and invalid inputs).

## Security Features

- **Input Validation**: All functions validate input types, lengths, and formats
- **Buffer Overflow Prevention**: Length checks on all binary data
- **DoS Protection**: Limits on data sizes and collection lengths
- **Type Safety**: Strict type checking with informative error messages
- **No Code Injection**: Use of bencode prevents code injection attacks
- **Cryptographically Secure RNG**: Uses `os.urandom()` for node ID generation

See `MEMORY/SECURITY_REVIEW_2025-10-24_bittorrent_dht_scraper.md` for detailed security analysis.

## Educational Value

This implementation is designed for learning and understanding:

1. **BitTorrent DHT Protocol**: Practical implementation of BEP 5
2. **Kademlia Algorithm**: XOR metric and K-bucket routing
3. **Network Programming**: UDP-based P2P communication patterns
4. **Data Serialization**: Bencode format used across BitTorrent ecosystem
5. **Distributed Systems**: DHT concepts and distributed lookups

## Limitations

While the scraper is fully functional, there are some limitations:

- **IPv4 only in compact format**: IPv6 support in Node class but not in wire protocol
- **No persistence**: Routing table is in-memory only (rebuilds on each run)
- **No NAT traversal**: Does not implement hole-punching or UPnP
- **Basic error handling**: Network errors are handled but could be more robust
- **No announce support**: Can find peers but cannot announce as a peer yourself

## References

- [BEP 3: The BitTorrent Protocol Specification](https://www.bittorrent.org/beps/bep_0003.html)
- [BEP 5: DHT Protocol](https://www.bittorrent.org/beps/bep_0005.html)
- [Kademlia Paper](https://pdos.csail.mit.edu/~petar/papers/maymounkov-kademlia-lncs.pdf)

## License

This is an educational project. Feel free to use it for learning purposes.

## Author

Created as an educational demonstration of BitTorrent DHT protocol implementation.

## Contributing

This is an educational project. Suggestions and improvements welcome!
