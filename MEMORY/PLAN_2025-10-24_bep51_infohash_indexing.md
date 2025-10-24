# Plan: BEP 51 DHT Infohash Indexing Support

**Date:** 2025-10-24
**Objective:** Implement BEP 51 to allow crawler to advertise indexing capability and exchange info_hash samples

## BEP 51 Overview

BEP 51 allows DHT nodes to advertise that they're indexing info_hashes by including a "samples" field in responses.

**Key Points:**
- Nodes that index info_hashes include "samples" in find_node/get_peers responses
- "samples" is a concatenated string of 20-byte info_hashes
- Receiving nodes can extract these samples to discover new info_hashes
- More efficient than waiting for get_peers queries

**Specification:**
- Field name: `samples` (binary string)
- Format: Concatenated 20-byte info_hashes (compact format)
- Max samples: ~20 samples per response (400 bytes)
- Included in: find_node responses, get_peers responses

## Current State

- Crawler discovers info_hashes passively by listening to get_peers queries
- No way to advertise indexing capability
- No way to receive samples from other indexing nodes
- Limited discovery rate

## Implementation Plan

### 1. Add Sample Packing Functions (protocol.py)

**New Functions:**
- `pack_samples(info_hashes: List[bytes]) -> bytes` - Pack list of info_hashes into compact format
- `unpack_samples(data: bytes) -> List[bytes]` - Unpack samples from binary data

**Validation:**
- Verify each info_hash is exactly 20 bytes
- Limit max samples to 20 (400 bytes total)
- Handle empty lists gracefully

### 2. Write Unit Tests (TDD)

**File:** `tests/test_protocol.py`

**Test Cases:**
- `test_pack_samples_empty()` - Empty list returns empty bytes
- `test_pack_samples_single()` - Single info_hash packs correctly
- `test_pack_samples_multiple()` - Multiple info_hashes pack correctly
- `test_pack_samples_max_limit()` - Respects 20 sample limit
- `test_pack_samples_invalid_length()` - Raises error for non-20-byte hashes
- `test_unpack_samples_empty()` - Empty data returns empty list
- `test_unpack_samples_single()` - Single sample unpacks correctly
- `test_unpack_samples_multiple()` - Multiple samples unpack correctly
- `test_unpack_samples_invalid_length()` - Raises error for non-multiple-of-20 data
- `test_pack_unpack_roundtrip()` - Roundtrip preserves data

**Minimum:** 10 new unit tests

### 3. Implement Sample Functions (protocol.py)

Implement functions to pass all unit tests.

### 4. Modify Response Functions (protocol.py)

**Update:**
- `_send_find_node_response()` - Add optional samples parameter
- `_send_get_peers_response()` - Add optional samples parameter

**Logic:**
- If crawler mode enabled and has discovered_info_hashes
- Sample up to 20 random info_hashes
- Pack into compact format
- Include in response dictionary

### 5. Integrate into DHT Client (dht_client.py)

**Modifications:**
- Add `enable_bep51` parameter to __init__ (default: False)
- Modify `_send_find_node_response()` calls to include samples
- Modify `_send_get_peers_response()` calls to include samples
- Add sample parsing in response handlers
- Add discovered samples to discovered_info_hashes
- Track BEP 51 discoveries separately

**New Tracking:**
- `bep51_samples_received` counter
- `bep51_samples_sent` counter
- Source tracking for BEP 51 discoveries

### 6. Add CLI Flag (scraper.py)

**Add argument:**
```python
parser.add_argument(
    '--enable-bep51',
    action='store_true',
    help='Enable BEP 51 DHT Infohash Indexing (exchange samples with other indexers)'
)
```

**Pass to client:**
```python
client = DHTClient(port=args.port, enable_bep51=args.enable_bep51)
```

### 7. Update Progress Display

**Add to progress line** (if BEP 51 enabled):
- BEP 51 samples received/sent count

### 8. Write E2E Test

**Test:** Verify --enable-bep51 flag works

### 9. Update Documentation

- README.md - Add BEP 51 usage examples
- CHANGELOG.md - Add under [Unreleased]
- Update help text

## Files to Modify/Create

1. **src/protocol.py** - Add pack_samples(), unpack_samples()
2. **src/dht_client.py** - Integrate BEP 51 support
3. **tests/test_protocol.py** - Add 10+ unit tests for samples
4. **scraper.py** - Add --enable-bep51 flag
5. **README.md** - Document BEP 51 usage
6. **CHANGELOG.md** - Add changes
7. **MEMORY/SECURITY_REVIEW_2025-10-24_bep51.md** - Security review

## Security Considerations

### Input Validation
- Validate samples field is bytes
- Check length is multiple of 20
- Limit to reasonable max (20 samples = 400 bytes)
- Prevent memory exhaustion

### DoS Protection
- Limit samples sent per response (max 20)
- Limit samples processed per response (max 20)
- Ignore malformed samples (don't crash)

### Privacy
- Random sampling prevents info_hash enumeration
- No personally identifiable information exposed

## Success Criteria

- [ ] 10+ unit tests for sample pack/unpack
- [ ] All 204+ tests passing
- [ ] --enable-bep51 flag working
- [ ] BEP 51 samples sent in responses
- [ ] BEP 51 samples parsed from responses
- [ ] Progress display shows BEP 51 stats (if enabled)
- [ ] Documentation updated
- [ ] CHANGELOG.md updated
- [ ] Security review completed

## Expected Benefits

- **Faster discovery:** Get samples from other indexers instead of waiting
- **More complete coverage:** Discover info_hashes not being actively searched
- **Better networking:** Exchange with other BEP 51 nodes
- **Standard compliant:** Follow official BEP 51 specification
