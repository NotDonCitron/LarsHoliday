#!/bin/bash

echo "=========================================="
echo "Holland Vacation Deal Finder - Test Suite"
echo "=========================================="
echo ""

echo "Test 1: Single city search (Amsterdam)"
echo "--------------------------------------"
python3 main.py --cities Amsterdam --checkin 2026-02-15 --checkout 2026-02-22 --output summary --top 3
echo ""

echo "Test 2: Multi-city search"
echo "--------------------------------------"
python3 main.py --cities "Amsterdam,Rotterdam,Utrecht" --checkin 2026-03-01 --checkout 2026-03-08 --output summary --top 3
echo ""

echo "Test 3: Budget constraint test"
echo "--------------------------------------"
python3 main.py --cities Zandvoort --checkin 2026-02-15 --checkout 2026-02-22 --budget-max 60 --output summary --top 3
echo ""

echo "Test 4: Small group (2 adults)"
echo "--------------------------------------"
python3 main.py --cities Amsterdam --checkin 2026-04-01 --checkout 2026-04-05 --adults 2 --pets 1 --output summary --top 3
echo ""

echo "Test 5: JSON output format"
echo "--------------------------------------"
python3 main.py --cities Rotterdam --checkin 2026-02-20 --checkout 2026-02-27 --top 2 | python3 -m json.tool | head -50
echo ""

echo "=========================================="
echo "Test Suite Complete"
echo "=========================================="
