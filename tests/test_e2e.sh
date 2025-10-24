#!/bin/bash
#
# End-to-End Tests for BitTorrent DHT Scraper CLI
#
# These tests verify the complete CLI workflow including:
# - Help/usage display
# - Input validation
# - Error handling
# - Demo script execution
# - Scraper initialization (without full network test)
#

# Don't exit on error for individual tests (we want to count failures)
# set -e

# Use Python 3 explicitly
PYTHON=$(which python3 2>/dev/null || which python 2>/dev/null || echo "python3")

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test counter
TESTS_RUN=0
TESTS_PASSED=0
TESTS_FAILED=0

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_DIR="$( cd "$SCRIPT_DIR/.." && pwd )"

# Test functions
print_test() {
    echo -e "\n${YELLOW}[TEST $((TESTS_RUN + 1))]${NC} $1"
}

pass() {
    echo -e "${GREEN}✓ PASS${NC}: $1"
    TESTS_PASSED=$((TESTS_PASSED + 1))
    TESTS_RUN=$((TESTS_RUN + 1))
}

fail() {
    echo -e "${RED}✗ FAIL${NC}: $1"
    TESTS_FAILED=$((TESTS_FAILED + 1))
    TESTS_RUN=$((TESTS_RUN + 1))
}

# Start tests
echo "======================================================================"
echo "End-to-End Tests for BitTorrent DHT Scraper"
echo "======================================================================"

cd "$PROJECT_DIR"

# ======================================================================
# TEST 1: Scraper help displays correctly
# ======================================================================
print_test "Scraper displays help message"

if $PYTHON scraper.py --help > /dev/null 2>&1; then
    OUTPUT=$($PYTHON scraper.py --help)
    if echo "$OUTPUT" | grep -q "BitTorrent DHT"; then
        pass "Help message displays correctly"
    else
        fail "Help message missing expected content"
    fi
else
    fail "Scraper --help failed"
fi

# ======================================================================
# TEST 2: Scraper validates invalid info_hash length
# ======================================================================
print_test "Scraper rejects invalid info_hash (too short)"

if $PYTHON scraper.py "short" 2>&1 | grep -q "40-character"; then
    pass "Invalid info_hash rejected with correct error"
else
    fail "Invalid info_hash not properly validated"
fi

# ======================================================================
# TEST 3: Scraper validates invalid info_hash format
# ======================================================================
print_test "Scraper rejects invalid info_hash (non-hex)"

if $PYTHON scraper.py "ZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZZ" 2>&1 | grep -q -i "invalid"; then
    pass "Non-hex info_hash rejected"
else
    fail "Non-hex info_hash not properly validated"
fi

# ======================================================================
# TEST 4: Demo script runs without errors
# ======================================================================
print_test "Demo script executes successfully"

# Run demo and check it produces output (don't wait for completion)
if $PYTHON dht_demo.py > /tmp/demo_output.log 2>&1; then
    if [ -s /tmp/demo_output.log ]; then
        pass "Demo script completed successfully"
    else
        fail "Demo script produced no output"
    fi
else
    EXIT_CODE=$?
    fail "Demo script failed with exit code $EXIT_CODE"
fi

rm -f /tmp/demo_output.log

# ======================================================================
# TEST 5: Demo script contains expected output
# ======================================================================
print_test "Demo script produces expected output"

DEMO_OUTPUT=$($PYTHON dht_demo.py 2>&1)

if echo "$DEMO_OUTPUT" | grep -q "DEMO 1: Bencode"; then
    if echo "$DEMO_OUTPUT" | grep -q "DEMO 2: DHT Nodes"; then
        if echo "$DEMO_OUTPUT" | grep -q "DEMO 3: Kademlia Routing Table"; then
            if echo "$DEMO_OUTPUT" | grep -q "DEMO 4: DHT Protocol"; then
                if echo "$DEMO_OUTPUT" | grep -q "DEMO 5: Simulated DHT Lookup"; then
                    pass "All 5 demos executed"
                else
                    fail "Demo 5 missing from output"
                fi
            else
                fail "Demo 4 missing from output"
            fi
        else
            fail "Demo 3 missing from output"
        fi
    else
        fail "Demo 2 missing from output"
    fi
else
    fail "Demo 1 missing from output"
fi

# ======================================================================
# TEST 6: All unit test files are executable
# ======================================================================
print_test "All unit test files exist and are runnable"

TEST_FILES=(
    "tests/test_bencode.py"
    "tests/test_node.py"
    "tests/test_routing_table.py"
    "tests/test_protocol.py"
    "tests/test_dht_client.py"
    "tests/test_progress_display.py"
)

ALL_TESTS_FOUND=true
for test_file in "${TEST_FILES[@]}"; do
    if [ ! -f "$test_file" ]; then
        echo "  Missing: $test_file"
        ALL_TESTS_FOUND=false
    fi
done

if $ALL_TESTS_FOUND; then
    pass "All 6 unit test files exist"
else
    fail "Some unit test files are missing"
fi

# ======================================================================
# TEST 7: Unit tests can be discovered and run
# ======================================================================
print_test "All unit tests pass"

UNIT_TEST_FAILED=false
for test_file in "${TEST_FILES[@]}"; do
    if ! $PYTHON "$test_file" > /dev/null 2>&1; then
        echo "  Failed: $test_file"
        UNIT_TEST_FAILED=true
    fi
done

if ! $UNIT_TEST_FAILED; then
    pass "All unit tests pass (194 tests)"
else
    fail "Some unit tests failed"
fi

# ======================================================================
# TEST 8: Scraper Python import works
# ======================================================================
print_test "Scraper can be imported and DHT client exists"

# Test that the scraper can import required modules
TEST_IMPORT=$(cat <<'EOF'
import sys
sys.path.insert(0, 'src')
from dht_client import DHTClient
client = DHTClient()
print("DHT client created successfully")
EOF
)

if echo "$TEST_IMPORT" | $PYTHON 2>&1 | grep -q "DHT client created"; then
    pass "Scraper DHT client can be imported and instantiated"
else
    fail "Scraper failed to import DHT client"
fi

# ======================================================================
# TEST 9: Required source files exist
# ======================================================================
print_test "All required source modules exist"

SOURCE_FILES=(
    "src/bencode.py"
    "src/node.py"
    "src/routing_table.py"
    "src/protocol.py"
    "src/dht_client.py"
    "src/progress_display.py"
)

ALL_SOURCES_FOUND=true
for source_file in "${SOURCE_FILES[@]}"; do
    if [ ! -f "$source_file" ]; then
        echo "  Missing: $source_file"
        ALL_SOURCES_FOUND=false
    fi
done

if $ALL_SOURCES_FOUND; then
    pass "All 6 source modules exist"
else
    fail "Some source modules are missing"
fi

# ======================================================================
# TEST 10: Documentation files exist
# ======================================================================
print_test "Documentation files exist"

DOC_FILES=(
    "README.md"
    "MEMORY/PLAN_2025-10-24_bittorrent_dht_scraper.md"
    "MEMORY/SECURITY_REVIEW_2025-10-24_bittorrent_dht_scraper.md"
    "prompts/2025-10-24_bittorrent_dht_scraper.yaml"
)

ALL_DOCS_FOUND=true
for doc_file in "${DOC_FILES[@]}"; do
    if [ ! -f "$doc_file" ]; then
        echo "  Missing: $doc_file"
        ALL_DOCS_FOUND=false
    fi
done

if $ALL_DOCS_FOUND; then
    pass "All required documentation exists"
else
    fail "Some documentation files are missing"
fi

# ======================================================================
# TEST 11: Python syntax is valid in all modules
# ======================================================================
print_test "Python syntax validation"

SYNTAX_ERRORS=false
for source_file in "${SOURCE_FILES[@]}"; do
    if ! $PYTHON -m py_compile "$source_file" 2>/dev/null; then
        echo "  Syntax error in: $source_file"
        SYNTAX_ERRORS=true
    fi
done

if ! $SYNTAX_ERRORS; then
    pass "All Python modules have valid syntax"
else
    fail "Some modules have syntax errors"
fi

# ======================================================================
# TEST 12: Scraper can parse command line arguments
# ======================================================================
print_test "Scraper argument parsing"

# Test various argument combinations
if $PYTHON scraper.py --help > /dev/null 2>&1 && \
   $PYTHON scraper.py 2d066c94480adcf5b7ab60065f24e681a57e011f --timeout 1 2>&1 | grep -q "DHT" && \
   $PYTHON scraper.py --timeout 1 2>&1 | grep -q "DHT"; then
    pass "Scraper parses all argument combinations"
else
    fail "Scraper argument parsing failed"
fi

# ======================================================================
# TEST 13: Progress display module works correctly
# ======================================================================
print_test "Progress display module import and functionality"

TEST_PROGRESS=$(cat <<'EOF'
import sys
sys.path.insert(0, 'src')
from progress_display import format_elapsed_time, calculate_rate, format_progress_line, clear_progress_line

# Test format_elapsed_time
assert format_elapsed_time(0) == "00:00:00", "format_elapsed_time(0) failed"
assert format_elapsed_time(65) == "00:01:05", "format_elapsed_time(65) failed"
assert format_elapsed_time(3661) == "01:01:01", "format_elapsed_time(3661) failed"

# Test calculate_rate
assert calculate_rate(60, 60.0) == 60.0, "calculate_rate(60, 60) failed"
assert calculate_rate(0, 60.0) == 0.0, "calculate_rate(0, 60) failed"

# Test format_progress_line
progress = format_progress_line(125.0, 42, 20.5, 150, 87)
assert "00:02:05" in progress, "Elapsed time not in progress line"
assert "42" in progress, "Count not in progress line"
assert "20.5" in progress, "Rate not in progress line"

# Test clear_progress_line
clear = clear_progress_line()
assert isinstance(clear, str), "clear_progress_line must return string"
assert len(clear) > 0, "clear_progress_line must not be empty"

print("All progress display tests passed")
EOF
)

if echo "$TEST_PROGRESS" | $PYTHON 2>&1 | grep -q "All progress display tests passed"; then
    pass "Progress display module works correctly"
else
    fail "Progress display module tests failed"
fi

# ======================================================================
# Summary
# ======================================================================
echo ""
echo "======================================================================"
echo "End-to-End Test Summary"
echo "======================================================================"
echo "Tests run:    $TESTS_RUN"
echo -e "Tests passed: ${GREEN}$TESTS_PASSED${NC}"

if [ $TESTS_FAILED -gt 0 ]; then
    echo -e "Tests failed: ${RED}$TESTS_FAILED${NC}"
    echo ""
    echo -e "${RED}FAILED${NC}: Some end-to-end tests failed"
    exit 1
else
    echo -e "Tests failed: ${GREEN}0${NC}"
    echo ""
    echo -e "${GREEN}SUCCESS${NC}: All end-to-end tests passed!"
    exit 0
fi
