# BitTorrent DHT Scraper - Claude Code Instructions

This file contains instructions for Claude Code when working on this repository.

## Project Overview

A BitTorrent DHT (Distributed Hash Table) scraper implemented in Python using only the standard library. The project demonstrates the Kademlia DHT protocol used by BitTorrent for distributed peer discovery.

**Key Features:**
- Dual operation modes: SCRAPER (find peers) and CRAWLER (discover info_hashes)
- Real-time progress display for infinite crawler mode
- BEP 51 DHT Infohash Indexing support
- Pure Python implementation (no external dependencies)

## Common Commands

### Development

```bash
# Run the scraper
python scraper.py --help                    # Show help
python scraper.py --timeout 0               # Infinite crawler mode
python scraper.py <info_hash>               # Find peers for torrent

# Run with custom parameters
python scraper.py --timeout 0 --query-interval 3    # Balanced visibility
python scraper.py --timeout 0 --query-interval 1    # Aggressive crawling
python scraper.py --port 6881                       # Specific port

# Run the demo
python dht_demo.py                          # Educational demonstration
```

### Testing

```bash
# Run all unit tests (194 total)
python tests/test_bencode.py               # 43 tests - Bencode encoding/decoding
python tests/test_node.py                  # 35 tests - DHT nodes and XOR distance
python tests/test_routing_table.py         # 34 tests - Kademlia routing table
python tests/test_protocol.py              # 36 tests - DHT protocol messages
python tests/test_dht_client.py            # 25 tests - DHT client functionality
python tests/test_progress_display.py      # 21 tests - Progress display formatting

# Run all tests at once
for test in tests/test_*.py; do python $test || exit 1; done

# Run end-to-end tests (13 tests)
bash tests/test_e2e.sh

# Run specific test class
python -m unittest tests.test_dht_client.TestCrawlNetworkQueryInterval
```

### Building and Deployment

```bash
# No build step required (pure Python)

# Check syntax
python -m py_compile src/*.py
python -m py_compile tests/*.py

# Make scripts executable
chmod +x scraper.py dht_demo.py tests/test_e2e.sh
```

## Code Architecture

### High-Level Structure

```
bt-dht/
├── src/                    # Core implementation modules
│   ├── bencode.py         # Bencode encoding/decoding (BEP 3)
│   ├── node.py            # DHT node representation + XOR distance
│   ├── routing_table.py   # Kademlia K-bucket routing table
│   ├── protocol.py        # DHT protocol messages (BEP 5, BEP 51)
│   ├── dht_client.py      # DHT client with network operations
│   └── progress_display.py # Real-time progress display
├── tests/                  # Test suite
│   ├── test_*.py          # Unit tests (194 total)
│   └── test_e2e.sh        # End-to-end tests (13 tests)
├── scraper.py             # Main CLI application
└── dht_demo.py            # Educational demonstration
```

### Key Components

**1. Bencode Module (`src/bencode.py`)**
- Encodes/decodes BitTorrent's data serialization format
- Handles: integers, byte strings, lists, dictionaries
- Used for all DHT message encoding

**2. Node Module (`src/node.py`)**
- Represents DHT network participants
- Implements XOR distance metric for Kademlia
- Validates node IDs, IP addresses, ports

**3. Routing Table (`src/routing_table.py`)**
- 160 K-buckets for 160-bit ID space
- LRU eviction policy when buckets are full
- Efficient closest node lookups

**4. Protocol Module (`src/protocol.py`)**
- Creates DHT queries: ping, find_node, get_peers
- Parses incoming DHT messages
- Implements BEP 5 (DHT Protocol) and BEP 51 (Infohash Indexing)
- Compact node format packing/unpacking

**5. DHT Client (`src/dht_client.py`)**
- Main client with UDP networking
- Bootstrap from known DHT nodes
- Iterative lookups for nodes and peers
- Crawler mode for info_hash discovery
- BEP 51 support for advertising indexing capability

**6. Progress Display (`src/progress_display.py`)**
- Real-time statistics formatting
- ANSI escape codes for in-place updates
- Elapsed time, rate calculation, progress lines

## Important Implementation Details

### DHT Protocol (BEP 5)

The scraper implements the mainline DHT protocol:
- **Kademlia-based** with XOR distance metric
- **Node IDs**: 160-bit identifiers (20 bytes)
- **Routing table**: 160 K-buckets, K=8 nodes per bucket
- **Messages**: ping, find_node, get_peers, announce_peer
- **Bootstrap nodes**: router.bittorrent.com, dht.transmissionbt.com

### BEP 51 Infohash Indexing

Nodes can advertise indexing capability:
- **samples** field in responses indicates indexing support
- Provides random sample of info_hashes being indexed
- Helps crawlers discover more info_hashes efficiently
- Implemented in `src/protocol.py` and `src/dht_client.py`

### Crawler Mode Operation

1. **Bootstrap**: Connect to known DHT nodes
2. **Populate routing table**: Exchange node information
3. **Active queries**: Send find_node to stay visible (configurable interval)
4. **Passive listening**: Receive get_peers queries from other nodes
5. **Discovery**: Extract info_hashes from incoming queries
6. **Progress tracking**: Display real-time statistics

### Rate Limiting

- **Progress updates**: 1 per second
- **Active queries**: Every `query_interval` seconds (default: 3)
- **Batch size**: 5 nodes per active query
- **Cleanup**: Old queries purged every 30 seconds
- **No limit on incoming discoveries** (passive)

## CHANGELOG.md Maintenance

**IMPORTANT**: Always update `CHANGELOG.md` when making changes to the codebase.

### Semantic Versioning Rules

This project follows [Semantic Versioning 2.0.0](https://semver.org/):

**Version format: MAJOR.MINOR.PATCH**

- **MAJOR**: Incompatible API changes (breaking changes)
- **MINOR**: New functionality in a backwards-compatible manner
- **PATCH**: Backwards-compatible bug fixes

### When to Increment

**MAJOR (X.0.0)** - Increment when:
- Removing public API features
- Changing function signatures in breaking ways
- Removing CLI arguments
- Changing default behavior in incompatible ways
- Example: Removing `--timeout` parameter, changing from Python 3 to Python 4

**MINOR (0.X.0)** - Increment when:
- Adding new features (new CLI arguments, new modes, new functions)
- Adding new modules
- Deprecating features (but not removing them)
- Example: Adding BEP 51 support, adding `--query-interval` parameter

**PATCH (0.0.X)** - Increment when:
- Bug fixes that don't change functionality
- Documentation updates
- Performance improvements
- Refactoring without API changes
- Example: Fixing progress display update frequency

### Changelog Entry Format

For each change, add entries under `## [Unreleased]` section:

```markdown
## [Unreleased]

### Added
- New features or capabilities

### Changed
- Changes to existing functionality

### Deprecated
- Features that will be removed in future versions

### Removed
- Features that were removed

### Fixed
- Bug fixes

### Security
- Security vulnerability fixes
```

### Changelog Update Process

1. **During Development**: Add changes under `## [Unreleased]`
2. **Before Release**:
   - Decide version number based on changes
   - Rename `[Unreleased]` to `[X.Y.Z] - YYYY-MM-DD`
   - Create new `[Unreleased]` section at top
   - Update comparison links at bottom

### Examples

**Adding new feature (MINOR bump):**
```markdown
## [Unreleased]

### Added
- BEP 51 DHT Infohash Indexing support in CRAWLER mode
- New `--sample-mode` parameter to enable BEP 51 sampling
```

**Fixing bug (PATCH bump):**
```markdown
## [Unreleased]

### Fixed
- Progress display now updates every second instead of only on discoveries
- Corrected elapsed time calculation in progress_display.py
```

**Breaking change (MAJOR bump):**
```markdown
## [Unreleased]

### Removed
- Deprecated `--old-parameter` CLI argument (use `--new-parameter` instead)

### Changed
- **BREAKING**: Changed default port from 6881 to random port for better compatibility
```

## Testing Requirements

### Test-Driven Development (TDD)

Always follow TDD when adding features:

1. **Write tests first** (red phase)
2. **Run tests to verify they fail**
3. **Implement feature** (green phase)
4. **Run tests to verify they pass**
5. **Refactor if needed**

### Test Coverage Requirements

- **Every function** must have at least **2 unit tests**:
  - 1 test for valid/expected behavior
  - 1 test for invalid input/error handling
- **Critical functions** (security, money, user data) need more edge case tests
- **New features** need at least 1 end-to-end test

### Running Tests Before Commit

**Always run ALL tests before committing:**

```bash
# Quick check - run all unit tests
for test in tests/test_*.py; do python $test || exit 1; done

# Full check - run all tests including E2E
for test in tests/test_*.py; do python $test || exit 1; done && bash tests/test_e2e.sh
```

## Security Considerations

### OWASP Top 10 Compliance

All code must follow OWASP Top 10 security best practices:

1. **Input Validation**: Validate all user inputs (CLI args, network data)
2. **Type Safety**: Check types before processing
3. **Range Checks**: Validate ranges for numbers, lengths for buffers
4. **No Code Injection**: Use safe bencode parsing, no eval/exec
5. **Resource Limits**: Prevent DoS with timeouts, size limits
6. **Cryptographic Security**: Use `os.urandom()` for node IDs

### Security Review Checklist

Before committing security-sensitive changes:

- [ ] Input validation added for all new parameters
- [ ] Type checking implemented
- [ ] Range/boundary checking in place
- [ ] No user input reaches eval/exec/system calls
- [ ] Resource consumption limited (timeouts, max sizes)
- [ ] Cryptographically secure RNG used where needed
- [ ] Security review document created in MEMORY/

## Common Development Tasks

### Adding a New CLI Parameter

1. Add argument to `scraper.py` argument parser
2. Update help text with examples
3. Pass parameter to relevant function
4. Add validation in function
5. Write unit tests for validation
6. Update README.md with usage
7. Update CHANGELOG.md

### Adding a New BEP/Protocol Feature

1. Research the BEP specification thoroughly
2. Add protocol message creation/parsing in `src/protocol.py`
3. Write unit tests for message encoding/decoding
4. Integrate into `src/dht_client.py`
5. Write integration tests
6. Update documentation
7. Add security review
8. Update CHANGELOG.md

### Fixing a Bug

1. Write a failing test that reproduces the bug
2. Fix the bug
3. Verify the test passes
4. Run all tests to ensure no regression
5. Update CHANGELOG.md under `### Fixed`

## Code Style and Conventions

- **Follow PEP 8** for Python code style
- **Type hints**: Use type hints in function signatures
- **Docstrings**: All functions must have docstrings
- **Error messages**: Be specific and helpful
- **No external dependencies**: Keep stdlib-only approach
- **Security first**: Validate all inputs

## Git Workflow

### Commit Message Format

```
<type>: <subject>

<body>

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>
```

**Types**: feat, fix, docs, style, refactor, test, chore

### Before Pushing

1. Run all tests
2. Update CHANGELOG.md
3. Update version number if releasing
4. Commit with descriptive message
5. Push to GitHub

## Resources

- [BEP 3: BitTorrent Protocol](https://www.bittorrent.org/beps/bep_0003.html)
- [BEP 5: DHT Protocol](https://www.bittorrent.org/beps/bep_0005.html)
- [BEP 51: DHT Infohash Indexing](https://www.bittorrent.org/beps/bep_0051.html)
- [Kademlia Paper](https://pdos.csail.mit.edu/~petar/papers/maymounkov-kademlia-lncs.pdf)
- [Semantic Versioning 2.0.0](https://semver.org/)
- [Keep a Changelog](https://keepachangelog.com/)

## Notes for Claude Code

- This project prioritizes **educational value** and **code clarity**
- **No external dependencies** - keep using only Python stdlib
- **Security is critical** - always validate inputs
- **Test coverage is mandatory** - follow TDD rigorously
- **Documentation is important** - update README and CHANGELOG
- When implementing new features, check existing patterns in codebase
- Always run tests before committing
- Keep commits atomic and well-documented
