"""
Pytest configuration and shared fixtures.

This module provides advanced configuration, custom reporters,
and shared utilities for the test suite.
"""

import pytest
import json
import os
from typing import Dict, List
from datetime import datetime
from pathlib import Path


test_results = []


class ViolationReporter:
    """Custom reporter for tracking API violations."""
    
    def __init__(self):
        self.violations = []
        self.passed_tests = []
        self.failed_tests = []
    
    def add_violation(self, test_name: str, endpoint: str, violations: List[str]):
        """Record a violation."""
        self.violations.append({
            "test_name": test_name,
            "endpoint": endpoint,
            "violations": violations,
            "timestamp": datetime.now().isoformat()
        })
        self.failed_tests.append(test_name)
    
    def add_passed(self, test_name: str, endpoint: str):
        """Record a passed test."""
        self.passed_tests.append({
            "test_name": test_name,
            "endpoint": endpoint,
            "timestamp": datetime.now().isoformat()
        })
    
    def generate_report(self, output_file: str = "violations_report.json"):
        """Generate a comprehensive violation report."""
        report = {
            "summary": {
                "total_tests": len(self.passed_tests) + len(self.failed_tests),
                "passed": len(self.passed_tests),
                "failed": len(self.failed_tests),
                "violation_count": len(self.violations),
                "generated_at": datetime.now().isoformat()
            },
            "passed_tests": self.passed_tests,
            "violations": self.violations
        }
        
        with open(output_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        return report


@pytest.fixture(scope="session")
def violation_reporter():
    """Session-scoped fixture for violation reporting."""
    return ViolationReporter()


@pytest.fixture(autouse=True)
def log_test_execution(request, violation_reporter):
    """Automatically log test execution results."""
    test_name = request.node.name
    
    yield
    
    if hasattr(request.node, 'rep_call'):
        if request.node.rep_call.passed:
            endpoint = test_name.replace("test_", "").replace("_", "/")
            violation_reporter.add_passed(test_name, endpoint)


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """Hook to capture test results."""
    outcome = yield
    report = outcome.get_result()
    if report.when == "call":
        item.rep_call = report


@pytest.fixture(scope="session", autouse=True)
def generate_violation_report(violation_reporter):
    """Generate violation report at the end of test session."""
    yield
    
    report = violation_reporter.generate_report()
    
    print("\n" + "="*80)
    print("API COMPARISON TEST SUMMARY")
    print("="*80)
    print(f"Total Tests: {report['summary']['total_tests']}")
    print(f"Passed: {report['summary']['passed']}")
    print(f"Failed: {report['summary']['failed']}")
    print(f"Violations Found: {report['summary']['violation_count']}")
    print("="*80)
    
    if report['violations']:
        print("\nVIOLATIONS DETECTED:")
        for violation in report['violations']:
            print(f"\n❌ {violation['test_name']}")
            print(f"   Endpoint: {violation['endpoint']}")
            print(f"   Violations: {len(violation['violations'])}")
    
    print(f"\n📊 Full report saved to: violations_report.json")
    print("="*80 + "\n")


@pytest.fixture(scope="session")
def base_urls():
    """Provide base URLs for APIs."""
    return {
        "dolos": os.getenv("DOLOS_BASE_URL", "http://localhost:3000"),
        "blockfrost": os.getenv("BLOCKFROST_BASE_URL", "https://cardano-preview.blockfrost.io/api/v0")
    }


@pytest.fixture(scope="session")
def blockfrost_api_key():
    """Provide Blockfrost API key."""
    api_key = os.getenv("BLOCKFROST_API_KEY")
    if not api_key or api_key == "your_blockfrost_api_key_here":
        pytest.skip("Blockfrost API key not configured")
    return api_key


def pytest_addoption(parser):
    """Add custom command line options."""
    parser.addoption(
        "--skip-slow",
        action="store_true",
        default=False,
        help="Skip slow tests"
    )
    parser.addoption(
        "--endpoint-filter",
        action="store",
        default=None,
        help="Run tests for specific endpoint pattern (e.g., 'blocks' or 'transactions')"
    )


def pytest_collection_modifyitems(config, items):
    """Modify test collection based on command line options."""
    if config.getoption("--skip-slow"):
        skip_slow = pytest.mark.skip(reason="--skip-slow option provided")
        for item in items:
            if "slow" in item.keywords:
                item.add_marker(skip_slow)
    
    endpoint_filter = config.getoption("--endpoint-filter")
    if endpoint_filter:
        skip_filtered = pytest.mark.skip(reason=f"endpoint filter '{endpoint_filter}' not matched")
        for item in items:
            if endpoint_filter.lower() not in item.name.lower():
                item.add_marker(skip_filtered)


def pytest_configure(config):
    """Register custom markers."""
    config.addinivalue_line(
        "markers", "critical: mark test as critical for production"
    )
    config.addinivalue_line(
        "markers", "requires_auth: mark test as requiring authentication"
    )
