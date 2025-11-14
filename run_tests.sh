#!/bin/bash

# Dolos vs Blockfrost API Comparison Test Runner
# This script provides convenient commands for running the test suite

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Functions
print_header() {
    echo -e "\n${BLUE}================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}================================${NC}\n"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

# Check if .env file exists
check_env() {
    if [ ! -f .env ]; then
        print_warning ".env file not found. Creating from .env.example..."
        cp .env.example .env
        print_warning "Please edit .env and add your BLOCKFROST_API_KEY"
        exit 1
    fi
    
    # Source the .env file
    export $(cat .env | grep -v '^#' | xargs)
    
    if [ -z "$BLOCKFROST_API_KEY" ] || [ "$BLOCKFROST_API_KEY" = "your_blockfrost_api_key_here" ]; then
        print_error "BLOCKFROST_API_KEY not configured in .env file"
        exit 1
    fi
    
    print_success "Environment configured"
}

# Check if dependencies are installed
check_dependencies() {
    print_header "Checking Dependencies"
    
    if ! command -v python3 &> /dev/null; then
        print_error "Python 3 is not installed"
        exit 1
    fi
    
    print_success "Python 3 found: $(python3 --version)"
    
    # Check if pytest is installed
    if ! python3 -c "import pytest" 2>/dev/null; then
        print_warning "pytest not found. Installing dependencies..."
        pip install -r requirements.txt
    else
        print_success "All dependencies installed"
    fi
}

# Display usage information
usage() {
    echo "Usage: $0 [command] [options]"
    echo ""
    echo "Commands:"
    echo "  all              Run all tests (default)"
    echo "  quick            Run tests with minimal output"
    echo "  verbose          Run tests with verbose output"
    echo "  category <name>  Run tests for specific category (blocks, txs, accounts, etc.)"
    echo "  single <name>    Run a single test by name"
    echo "  report           Generate HTML and JSON reports"
    echo "  parallel         Run tests in parallel (faster)"
    echo "  watch            Watch mode - run tests on file changes"
    echo "  clean            Clean up generated reports"
    echo "  setup            Setup environment and install dependencies"
    echo "  help             Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 all                    # Run all tests"
    echo "  $0 category blocks        # Run only block-related tests"
    echo "  $0 single network_eras    # Run single test"
    echo "  $0 report                 # Generate detailed reports"
    echo "  $0 parallel               # Run tests in parallel"
}

# Run all tests
run_all() {
    print_header "Running All Tests"
    check_env
    pytest test_dolos_vs_blockfrost.py -v
}

# Run tests with minimal output
run_quick() {
    print_header "Running Quick Test"
    check_env
    pytest test_dolos_vs_blockfrost.py -q
}

# Run tests with verbose output
run_verbose() {
    print_header "Running Verbose Tests"
    check_env
    pytest test_dolos_vs_blockfrost.py -vv --tb=long
}

# Run tests by category
run_category() {
    local category=$1
    if [ -z "$category" ]; then
        print_error "Please specify a category"
        echo "Available categories: blocks, txs, accounts, assets, pools, governance, network, metadata"
        exit 1
    fi
    
    print_header "Running Tests for Category: $category"
    check_env
    pytest test_dolos_vs_blockfrost.py -v -k "$category"
}

# Run single test
run_single() {
    local test_name=$1
    if [ -z "$test_name" ]; then
        print_error "Please specify a test name"
        exit 1
    fi
    
    print_header "Running Test: $test_name"
    check_env
    pytest test_dolos_vs_blockfrost.py::test_$test_name -vv
}

# Generate reports
run_report() {
    print_header "Generating Comprehensive Reports"
    check_env
    pytest test_dolos_vs_blockfrost.py -v --html=report.html --self-contained-html --json-report --json-report-file=report.json
    print_success "Reports generated:"
    echo "  - report.html (Visual HTML report)"
    echo "  - report.json (Machine-readable JSON)"
    echo "  - violations_report.json (Violation details)"
}

# Run tests in parallel
run_parallel() {
    print_header "Running Tests in Parallel"
    
    # Check if pytest-xdist is installed
    if ! python3 -c "import xdist" 2>/dev/null; then
        print_warning "pytest-xdist not found. Installing..."
        pip install pytest-xdist
    fi
    
    check_env
    pytest test_dolos_vs_blockfrost.py -v -n auto
}

# Watch mode
run_watch() {
    print_header "Watch Mode - Tests will run on file changes"
    
    # Check if pytest-watch is installed
    if ! command -v ptw &> /dev/null; then
        print_warning "pytest-watch not found. Installing..."
        pip install pytest-watch
    fi
    
    check_env
    ptw test_dolos_vs_blockfrost.py -- -v
}

# Clean up reports
clean_reports() {
    print_header "Cleaning Up Reports"
    rm -f report.html report.json violations_report.json .pytest_cache
    rm -rf __pycache__ .pytest_cache
    print_success "Reports cleaned"
}

# Setup environment
setup_env() {
    print_header "Setting Up Environment"
    
    # Create .env if it doesn't exist
    if [ ! -f .env ]; then
        cp .env.example .env
        print_success ".env file created"
    fi
    
    # Install dependencies
    print_header "Installing Dependencies"
    pip install -r requirements.txt
    print_success "Dependencies installed"
    
    print_header "Setup Complete"
    print_warning "Please edit .env and add your BLOCKFROST_API_KEY"
}

# Main command handler
case "${1:-all}" in
    all)
        check_dependencies
        run_all
        ;;
    quick)
        check_dependencies
        run_quick
        ;;
    verbose)
        check_dependencies
        run_verbose
        ;;
    category)
        check_dependencies
        run_category "$2"
        ;;
    single)
        check_dependencies
        run_single "$2"
        ;;
    report)
        check_dependencies
        run_report
        ;;
    parallel)
        check_dependencies
        run_parallel
        ;;
    watch)
        check_dependencies
        run_watch
        ;;
    clean)
        clean_reports
        ;;
    setup)
        setup_env
        ;;
    help|--help|-h)
        usage
        ;;
    *)
        print_error "Unknown command: $1"
        usage
        exit 1
        ;;
esac
