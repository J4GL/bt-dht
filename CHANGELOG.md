# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Demo 6 in dht_demo.py: BEP 51 sample packing/unpacking demonstration

## [0.4.0] - 2025-10-24

### Added
- BEP 51 DHT Infohash Indexing support in CRAWLER mode (enabled by default)
- `pack_samples()` and `unpack_samples()` functions for BEP 51 sample encoding
- Sample exchange in find_node and get_peers responses
- BEP 51 statistics tracking (samples sent/received, BEP 51 discoveries)
- CHANGELOG.md following Semantic Versioning Specification (v2.0.0)
- CLAUDE.md with comprehensive project documentation and development guidelines
- 12 new unit tests for BEP 51 sample packing/unpacking (206 total unit tests)

### Changed
- DHT responses now include info_hash samples when crawler mode is active
- Crawler discovers info_hashes both passively (get_peers) and actively (BEP 51 samples)
- Results display now shows BEP 51 statistics when enabled

## [0.3.0] - 2025-10-24

### Added
- Configurable `--query-interval` parameter for crawler mode (default: 3 seconds)
- 6 new unit tests for query_interval validation (194 total unit tests)

### Changed
- Default active query interval from 10 seconds to 3 seconds
- Improved DHT visibility with more frequent queries

## [0.2.0] - 2025-10-24

### Added
- Real-time progress display for INFINITE crawler mode
- Progress metrics: elapsed time, discovery rate, request count, routing table size
- 21 unit tests for progress_display module
- `src/progress_display.py` module

### Fixed
- Progress display now updates continuously every second (not just on discoveries)
- Added `progress_callback` parameter to `crawl_network()` method

## [0.1.0] - 2025-10-24

### Added
- Initial BitTorrent DHT scraper implementation
- Two operation modes:
  - SCRAPER mode: Find peers for specific torrents
  - CRAWLER mode: Discover info_hashes being shared on DHT
- Core modules:
  - `src/bencode.py` - Bencode encoding/decoding (BEP 3)
  - `src/node.py` - DHT node representation with XOR distance
  - `src/routing_table.py` - Kademlia K-bucket routing table
  - `src/protocol.py` - DHT protocol message handling (BEP 5)
  - `src/dht_client.py` - Complete DHT client with network operations
- Comprehensive testing:
  - 188 unit tests (43 bencode, 35 node, 34 routing_table, 36 protocol, 19 dht_client, 21 progress_display)
  - 13 end-to-end tests
- Documentation:
  - Complete README.md with usage examples
  - Implementation plans and security reviews
  - Optimized prompts for development

### Security
- OWASP Top 10 compliant implementation
- Input validation on all parameters
- No code injection vulnerabilities
- Cryptographically secure RNG for node IDs

[Unreleased]: https://github.com/J4GL/bt-dht/compare/v0.4.0...HEAD
[0.4.0]: https://github.com/J4GL/bt-dht/compare/v0.3.0...v0.4.0
[0.3.0]: https://github.com/J4GL/bt-dht/compare/v0.2.0...v0.3.0
[0.2.0]: https://github.com/J4GL/bt-dht/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/J4GL/bt-dht/releases/tag/v0.1.0
