# Plan: Enhanced Progress Display for CRAWLER Mode with INFINITE Duration

**Date:** 2025-10-24
**Objective:** Add comprehensive real-time progress display for BitTorrent DHT crawler when running indefinitely

## Analysis

Current state:
- scraper.py lines 206-268 handle CRAWLER mode
- Basic discovery output: `[count] info_hash (from IP)`
- No real-time statistics or progress indicators
- No elapsed time, rate, or network stats

## Implementation Plan

### 1. Create Progress Display Module
- **File:** `src/progress_display.py`
- **Functions needed:**
  - `format_elapsed_time(seconds: float) -> str` - Format seconds as HH:MM:SS
  - `calculate_rate(count: int, elapsed: float) -> float` - Calculate items per minute
  - `format_progress_line(elapsed, count, rate, total_requests, table_size) -> str` - Format the progress line
  - `clear_progress_line() -> str` - Return ANSI code to clear current line

### 2. Write Unit Tests First (TDD)
- **File:** `tests/test_progress_display.py`
- **Test cases:**
  - Test `format_elapsed_time()` with various durations (0s, 59s, 3661s)
  - Test `calculate_rate()` with different counts and elapsed times
  - Test `format_progress_line()` output format
  - Test edge cases: zero elapsed time, zero count
  - Test invalid inputs (negative values, etc.)

### 3. Implement Progress Display Functions
- Write implementations to pass all unit tests
- Use ANSI escape codes for in-place updates
- Handle edge cases properly

### 4. Integrate into scraper.py
- Modify CRAWLER mode section (lines 206-268)
- Add progress line that updates every N discoveries or every second
- Keep existing line-by-line output
- Add final summary with statistics
- Ensure clean Ctrl+C handling

### 5. Write End-to-End Test
- **File:** `tests/test_e2e_progress.sh`
- Test infinite crawler mode shows progress (run for 5 seconds then Ctrl+C)
- Verify output contains progress indicators
- Verify graceful shutdown

### 6. Test and Validate
- Run all unit tests
- Run end-to-end test
- Manual testing with actual DHT network

## Files to Modify/Create

1. **CREATE:** `src/progress_display.py` - New module for progress display
2. **CREATE:** `tests/test_progress_display.py` - Unit tests (at least 8 tests)
3. **MODIFY:** `scraper.py` - Integrate progress display into CRAWLER mode
4. **CREATE:** `tests/test_e2e_progress.sh` - E2E test for progress display

## Security Considerations

- Display-only functionality, no new attack surface
- Input validation on all parameters
- No user input processing
- No file I/O or network operations in display code
- Safe handling of ANSI escape codes

## Success Criteria

- [ ] At least 8 unit tests written and passing
- [ ] All functions have 2+ unit tests (valid and invalid inputs)
- [ ] Progress display shows: elapsed time, count, rate, requests, table size
- [ ] Display updates in real-time during infinite crawl
- [ ] Clean output on Ctrl+C interrupt
- [ ] E2E test passes
- [ ] All existing tests still pass
- [ ] Code follows OWASP best practices
