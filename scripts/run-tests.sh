#!/bin/bash
# テスト実行スクリプト

set -e

echo "=========================================="
echo "MrWebDefence LogServer - Test Runner"
echo "=========================================="

# カラーコード
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# テストタイプを引数から取得（デフォルト: all）
TEST_TYPE=${1:-all}

run_unit_tests() {
    echo -e "${YELLOW}Running Unit Tests...${NC}"
    poetry run pytest tests/unit/ -v --tb=short
}

run_integration_tests() {
    echo -e "${YELLOW}Running Integration Tests...${NC}"
    poetry run pytest tests/integration/ -v --tb=short
}

run_all_tests() {
    echo -e "${YELLOW}Running All Tests...${NC}"
    poetry run pytest tests/ -v --tb=short
}

run_coverage() {
    echo -e "${YELLOW}Running Tests with Coverage...${NC}"
    poetry run pytest tests/ -v --cov=src --cov-report=html --cov-report=term
    echo -e "${GREEN}Coverage report generated in htmlcov/index.html${NC}"
}

case "$TEST_TYPE" in
    unit)
        run_unit_tests
        ;;
    integration)
        run_integration_tests
        ;;
    coverage)
        run_coverage
        ;;
    all)
        run_all_tests
        ;;
    *)
        echo -e "${RED}Unknown test type: $TEST_TYPE${NC}"
        echo "Usage: $0 [unit|integration|coverage|all]"
        exit 1
        ;;
esac

echo -e "${GREEN}✓ Tests completed successfully!${NC}"
