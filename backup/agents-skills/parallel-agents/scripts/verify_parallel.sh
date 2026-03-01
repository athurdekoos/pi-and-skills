#!/bin/bash
# Verification script for parallel agent test (eval 1)
# Run this after the parallel agents have completed to check results

set -e

PASS=0
FAIL=0

check_file() {
    local file="$1"
    local expected="$2"
    local label="$3"
    
    if [ ! -f "$file" ]; then
        echo "FAIL: $label - file $file does not exist"
        FAIL=$((FAIL + 1))
        return
    fi
    
    content=$(cat "$file")
    if echo "$content" | grep -q "$expected"; then
        echo "PASS: $label - $file contains '$expected'"
        PASS=$((PASS + 1))
    else
        echo "FAIL: $label - $file contains '$content', expected '$expected'"
        FAIL=$((FAIL + 1))
    fi
}

echo "=== Parallel Agent Verification ==="
echo ""

# Eval 1 files
echo "--- Eval 1: Three parallel workers ---"
check_file "/tmp/parallel-test-alpha.txt" "ALPHA" "Agent 1 output"
check_file "/tmp/parallel-test-bravo.txt" "BRAVO" "Agent 2 output"
check_file "/tmp/parallel-test-charlie.txt" "CHARLIE" "Agent 3 output"

echo ""

# Eval 3 files
echo "--- Eval 3: Four math workers ---"
check_file "/tmp/math-1.txt" "100" "Math worker 1"
check_file "/tmp/math-2.txt" "256" "Math worker 2"
check_file "/tmp/math-3.txt" "42" "Math worker 3"
check_file "/tmp/math-4.txt" "3.14" "Math worker 4"

echo ""
echo "=== Results: $PASS passed, $FAIL failed ==="

if [ $FAIL -gt 0 ]; then
    exit 1
fi
