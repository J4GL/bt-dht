# Plan: Configurable Active Query Interval for DHT Crawler

**Date:** 2025-10-24
**Objective:** Add --query-interval parameter and change default from 10 to 3 seconds

## Current State

- Active queries sent every 10 iterations (hardcoded)
- Each iteration = 1 second
- No way to configure this behavior
- Line 547 in dht_client.py: `if query_count % 10 == 0:`

## Implementation Plan

### 1. Modify DHTClient.crawl_network()
- **File:** `src/dht_client.py`
- Add `query_interval` parameter with default value of 3
- Replace hardcoded `10` with `query_interval`
- Add parameter validation

### 2. Update scraper.py
- **File:** `scraper.py`
- Add `--query-interval` argument to argument parser
- Pass interval to `crawl_network()` method
- Add help text explaining the parameter

### 3. Write Unit Tests (TDD)
- **File:** `tests/test_dht_client.py`
- Test valid query intervals (1, 3, 10, 30)
- Test invalid intervals (0, -1, non-integer)
- Test that parameter is properly used

### 4. Run All Tests
- Ensure all 188 unit tests still pass
- Ensure all 13 E2E tests still pass

### 5. Update Documentation
- Update README.md with new parameter
- Add example usage

## Files to Modify

1. **src/dht_client.py** - Add query_interval parameter
2. **scraper.py** - Add CLI argument
3. **tests/test_dht_client.py** - Add validation tests
4. **README.md** - Document new parameter

## Changes in Detail

### Change 1: dht_client.py

**Before:**
```python
def crawl_network(self, duration: float = 60.0, callback: Callable = None, progress_callback: Callable = None):
    ...
    if query_count % 10 == 0:  # Every 10 iterations
```

**After:**
```python
def crawl_network(self, duration: float = 60.0, callback: Callable = None, progress_callback: Callable = None, query_interval: int = 3):
    # Validate query_interval
    if not isinstance(query_interval, int) or query_interval < 1:
        raise ValueError("query_interval must be a positive integer >= 1")
    ...
    if query_count % query_interval == 0:  # Every query_interval iterations
```

### Change 2: scraper.py

**Add argument:**
```python
parser.add_argument(
    '--query-interval',
    type=int,
    default=3,
    help='Active query interval in seconds (default: 3, min: 1)'
)
```

**Pass to crawl_network:**
```python
results = client.crawl_network(
    duration=args.timeout,
    callback=on_discovery,
    progress_callback=on_progress if infinite_mode else None,
    query_interval=args.query_interval
)
```

## Security Considerations

- **Minimum value:** 1 second (prevent network flooding)
- **Type validation:** Must be integer
- **Range validation:** Must be positive
- **Impact:** Lower values = more visibility but more network traffic

**Recommended values:**
- 1-2 seconds: Maximum visibility (aggressive)
- 3-5 seconds: High visibility (balanced) ⭐ NEW DEFAULT
- 10+ seconds: Low network usage (conservative)

## Testing Strategy

1. Write tests first (TDD)
2. Run tests - should fail
3. Implement changes
4. Run tests - should pass
5. Manual testing with real DHT network

## Success Criteria

- [ ] query_interval parameter added to crawl_network()
- [ ] --query-interval CLI argument added
- [ ] Default changed from 10 to 3 seconds
- [ ] Input validation implemented
- [ ] Unit tests added and passing
- [ ] All existing tests still pass
- [ ] Documentation updated
