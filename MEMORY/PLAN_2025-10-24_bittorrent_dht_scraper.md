# BitTorrent DHT Scraper Implementation Plan

## Project Overview
Build a CLI BitTorrent DHT scraper in Python using only standard library components for educational purposes. The scraper will implement the Kademlia DHT protocol (BEP 5) to discover peers in the BitTorrent network.

## Architecture

### Module Structure
```
bt-dht/
├── src/
│   ├── bencode.py          # Bencode encoding/decoding
│   ├── node.py             # DHT Node representation
│   ├── routing_table.py    # Kademlia routing table (K-buckets)
│   ├── protocol.py         # DHT protocol messages
│   ├── dht_client.py       # Main DHT client/scraper
│   └── cli.py              # Command-line interface
├── tests/
│   ├── test_bencode.py
│   ├── test_node.py
│   ├── test_routing_table.py
│   ├── test_protocol.py
│   ├── test_dht_client.py
│   └── test_e2e.sh
├── prompts/
│   └── 2025-10-24_bittorrent_dht_scraper.yaml
├── MEMORY/
│   ├── PLAN_2025-10-24_bittorrent_dht_scraper.md (this file)
│   └── SECURITY_REVIEW_2025-10-24_bittorrent_dht_scraper.md (to be created)
└── README.md

```

## Implementation Steps

### Phase 1: Bencode Implementation (src/bencode.py)
**Functions to implement:**
1. `encode(obj)` - Encode Python objects to bencode format
   - Handle integers, bytes, lists, dicts
   - Raise TypeError for unsupported types

2. `decode(data)` - Decode bencode data to Python objects
   - Parse integers (i<num>e)
   - Parse byte strings (<length>:<string>)
   - Parse lists (l<contents>e)
   - Parse dicts (d<contents>e)
   - Raise ValueError for malformed data

**Unit Tests (minimum 2 per function = 4 tests):**
- test_encode_valid_data (integers, strings, lists, dicts)
- test_encode_invalid_data (unsupported types)
- test_decode_valid_data (all bencode types)
- test_decode_invalid_data (malformed bencode)

### Phase 2: Node Representation (src/node.py)
**Functions to implement:**
1. `__init__(node_id, ip, port)` - Initialize a DHT node
   - Validate node_id (20 bytes)
   - Validate IP address format
   - Validate port range (1-65535)

2. `distance(node_id1, node_id2)` - Calculate XOR distance between node IDs
   - Used by Kademlia for routing

3. `generate_node_id()` - Generate random 20-byte node ID

4. `__eq__`, `__hash__`, `__repr__` - Standard Python methods

**Unit Tests (minimum 8 tests):**
- test_node_creation_valid
- test_node_creation_invalid_id
- test_node_creation_invalid_ip
- test_node_creation_invalid_port
- test_distance_calculation
- test_distance_symmetry
- test_generate_node_id
- test_node_equality

### Phase 3: Routing Table (src/routing_table.py)
**Functions to implement:**
1. `__init__(node_id, k=8)` - Initialize routing table with K-buckets
   - K = maximum nodes per bucket (default 8)
   - 160 buckets (for 160-bit node IDs)

2. `add_node(node)` - Add a node to appropriate K-bucket
   - Calculate bucket index using XOR distance
   - Implement bucket splitting if needed
   - LRU eviction if bucket full

3. `get_closest_nodes(target_id, count=8)` - Get closest nodes to target
   - Search across buckets
   - Sort by XOR distance

4. `remove_node(node)` - Remove a node from routing table

5. `get_bucket_index(node_id)` - Calculate which bucket a node belongs to

**Unit Tests (minimum 10 tests):**
- test_routing_table_init
- test_add_node_to_empty_bucket
- test_add_node_bucket_full
- test_get_closest_nodes
- test_get_closest_nodes_empty_table
- test_remove_node_exists
- test_remove_node_not_exists
- test_bucket_index_calculation
- test_multiple_nodes_same_bucket
- test_routing_table_size_limit

### Phase 4: DHT Protocol Messages (src/protocol.py)
**Functions to implement:**
1. `create_ping_query(transaction_id, node_id)` - Create ping query
2. `create_ping_response(transaction_id, node_id)` - Create ping response
3. `create_find_node_query(transaction_id, node_id, target_id)` - Create find_node query
4. `create_find_node_response(transaction_id, node_id, nodes)` - Create find_node response
5. `create_get_peers_query(transaction_id, node_id, info_hash)` - Create get_peers query
6. `create_get_peers_response(transaction_id, node_id, token, peers=None, nodes=None)` - Create get_peers response
7. `parse_message(data)` - Parse incoming DHT message
8. `pack_nodes(nodes)` - Pack node list into compact format (26 bytes per node for IPv4)
9. `unpack_nodes(data)` - Unpack compact node format
10. `pack_peers(peers)` - Pack peer list into compact format (6 bytes per peer for IPv4)
11. `unpack_peers(data)` - Unpack compact peer format
12. `validate_message(msg)` - Validate message structure

**Unit Tests (minimum 24 tests):**
- test_create_ping_query
- test_create_ping_response
- test_create_find_node_query
- test_create_find_node_response
- test_create_get_peers_query
- test_create_get_peers_response
- test_parse_valid_query
- test_parse_valid_response
- test_parse_invalid_message
- test_parse_malformed_bencode
- test_pack_nodes_ipv4
- test_unpack_nodes_ipv4
- test_pack_nodes_invalid_data
- test_unpack_nodes_invalid_data
- test_pack_peers_ipv4
- test_unpack_peers_ipv4
- test_pack_peers_invalid_data
- test_unpack_peers_invalid_data
- test_validate_message_valid
- test_validate_message_missing_fields
- test_validate_message_wrong_types
- test_transaction_id_handling
- test_message_type_detection
- test_error_message_handling

### Phase 5: DHT Client/Scraper (src/dht_client.py)
**Functions to implement:**
1. `__init__(port=6881, bootstrap_nodes=None)` - Initialize DHT client
   - Create UDP socket
   - Generate node ID
   - Initialize routing table
   - Set bootstrap nodes

2. `start()` - Start the DHT client
   - Bind socket
   - Start bootstrap process
   - Start message handler thread

3. `stop()` - Stop the DHT client
   - Close socket
   - Clean shutdown

4. `bootstrap()` - Bootstrap DHT node
   - Send find_node queries to bootstrap nodes
   - Populate routing table

5. `send_ping(node)` - Send ping to a node
6. `send_find_node(node, target_id)` - Send find_node query
7. `send_get_peers(node, info_hash)` - Send get_peers query
8. `handle_message(data, addr)` - Handle incoming messages
9. `scrape_peers(info_hash, timeout=30)` - Main scraping function
   - Search DHT for peers with given info_hash
   - Return list of discovered peers

10. `handle_ping_query(msg, addr)` - Handle incoming ping
11. `handle_find_node_query(msg, addr)` - Handle incoming find_node
12. `handle_get_peers_query(msg, addr)` - Handle incoming get_peers
13. `handle_ping_response(msg, addr)` - Handle ping response
14. `handle_find_node_response(msg, addr)` - Handle find_node response
15. `handle_get_peers_response(msg, addr)` - Handle get_peers response

**Unit Tests (minimum 30 tests):**
- test_dht_client_init
- test_dht_client_init_custom_port
- test_start_client
- test_stop_client
- test_send_ping_valid_node
- test_send_ping_invalid_node
- test_send_find_node
- test_send_get_peers
- test_handle_ping_query
- test_handle_ping_response
- test_handle_find_node_query
- test_handle_find_node_response
- test_handle_get_peers_query
- test_handle_get_peers_response_with_peers
- test_handle_get_peers_response_with_nodes
- test_handle_malformed_message
- test_bootstrap_with_nodes
- test_bootstrap_no_nodes
- test_scrape_peers_found
- test_scrape_peers_not_found
- test_scrape_peers_timeout
- test_transaction_id_matching
- test_routing_table_updates
- test_socket_error_handling
- test_concurrent_requests
- test_rate_limiting
- test_node_cleanup
- test_message_queue
- test_response_timeout
- test_duplicate_message_handling

### Phase 6: CLI Interface (src/cli.py)
**Functions to implement:**
1. `main()` - Main CLI entry point
   - Parse command-line arguments
   - Initialize DHT client
   - Execute scrape operation
   - Display results

2. `parse_arguments()` - Parse CLI arguments
   - info_hash (required)
   - --port (optional)
   - --bootstrap (optional)
   - --timeout (optional)
   - --verbose (optional)

3. `validate_info_hash(hash_str)` - Validate info hash format
   - Must be 40-char hex string or 32-char base32
   - Convert to 20 bytes

4. `format_results(peers, nodes)` - Format and display results

5. `setup_logging(verbose)` - Setup logging configuration

**Unit Tests (minimum 10 tests):**
- test_parse_arguments_minimal
- test_parse_arguments_full
- test_parse_arguments_invalid
- test_validate_info_hash_hex
- test_validate_info_hash_base32
- test_validate_info_hash_invalid
- test_format_results_with_peers
- test_format_results_no_peers
- test_setup_logging_verbose
- test_setup_logging_quiet

### Phase 7: End-to-End Testing (tests/test_e2e.sh)
**Test scenarios:**
1. Start DHT client with default bootstrap nodes
2. Search for a known info hash
3. Verify peers are discovered
4. Test error handling for invalid info hash
5. Test timeout handling

### Phase 8: Security Review
**Areas to review:**
1. Input validation for all network data
2. Buffer overflow prevention
3. DoS protection (rate limiting)
4. Node ID validation
5. Info hash validation
6. IP address validation
7. Port validation
8. Message size limits
9. Transaction ID collision handling
10. Socket timeout configuration

## Success Criteria
- All unit tests pass (minimum 2 per function)
- All end-to-end tests pass
- Security review completed with no critical issues
- All functions have comprehensive docstrings
- Code follows PEP 8
- No external dependencies (only stdlib)

## Estimated Function Count
- bencode.py: 2 functions
- node.py: 5 functions
- routing_table.py: 5 functions
- protocol.py: 12 functions
- dht_client.py: 15 functions
- cli.py: 5 functions
**Total: ~44 functions**
**Minimum unit tests required: ~88 tests**

## Implementation Order
1. bencode.py (foundation)
2. node.py (basic building block)
3. routing_table.py (depends on node)
4. protocol.py (depends on bencode, node)
5. dht_client.py (depends on all above)
6. cli.py (depends on dht_client)
7. Unit tests (parallel with implementation)
8. End-to-end tests
9. Security review
