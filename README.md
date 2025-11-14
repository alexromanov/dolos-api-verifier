# Dolos vs Blockfrost API Comparison Test Suite

This test suite compares the responses from Dolos API and Blockfrost API endpoints to ensure data consistency and identify any violations.

## Overview

The test suite performs the following for each endpoint:
1. Calls the Dolos API endpoint
2. Calls the corresponding Blockfrost API endpoint
3. Compares the JSON responses using deep comparison
4. Reports any data violations or discrepancies

## Prerequisites

- Python 3.8+
- Dolos API running at `http://localhost:3000` (or custom URL)
- Blockfrost API key for Cardano Preview network

## Installation

1. Clone or download the test suite files

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Configure environment variables:
```bash
cp .env.example .env
# Edit .env and add your BLOCKFROST_API_KEY
```

## Configuration

### Environment Variables

Create a `.env` file with the following variables:

```bash
# Required: Your Blockfrost API key
BLOCKFROST_API_KEY=your_blockfrost_api_key_here

# Optional: Custom base URLs
DOLOS_BASE_URL=http://localhost:3000
BLOCKFROST_BASE_URL=https://cardano-preview.blockfrost.io/api/v0
```

### Getting a Blockfrost API Key

1. Visit https://blockfrost.io
2. Sign up for a free account
3. Create a new project for "Cardano Preview" network
4. Copy your project API key

## Usage

### Run All Tests

```bash
pytest test_dolos_vs_blockfrost.py
```

### Run with Verbose Output

```bash
pytest test_dolos_vs_blockfrost.py -v
```

### Run Specific Test

```bash
pytest test_dolos_vs_blockfrost.py::test_network_eras -v
```

### Run Tests by Category

```bash
# Only block-related tests
pytest test_dolos_vs_blockfrost.py -k "blocks"

# Only transaction-related tests
pytest test_dolos_vs_blockfrost.py -k "tx"

# Only account-related tests
pytest test_dolos_vs_blockfrost.py -k "account"
```

### Run with HTML Report

```bash
pytest test_dolos_vs_blockfrost.py --html=report.html --self-contained-html
```

### Run with Custom Endpoint Filter

```bash
pytest --endpoint-filter=blocks
pytest --endpoint-filter=transactions
```

### Parallel Execution (Faster)

```bash
pip install pytest-xdist
pytest test_dolos_vs_blockfrost.py -n auto
```

## Test Coverage

The test suite covers the following endpoint categories:

### Network Endpoints (2 tests)
- `/network`
- `/network/eras`

### Block Endpoints (8 tests)
- `/blocks/latest`
- `/blocks/{block_id}`
- `/blocks/{block_id}/next`
- `/blocks/{block_id}/previous`
- `/blocks/{block_id}/txs`
- `/blocks/latest/txs`
- `/blocks/slot/{slot_number}`

### Transaction Endpoints (12 tests)
- `/txs/{hash}`
- `/txs/{hash}/cbor`
- `/txs/{hash}/utxos`
- `/txs/{hash}/metadata`
- `/txs/{hash}/metadata/cbor`
- `/txs/{hash}/mirs`
- `/txs/{hash}/withdrawals`
- `/txs/{hash}/delegations`
- `/txs/{hash}/stakes`
- `/txs/{hash}/pool_retires`
- `/txs/{hash}/pool_updates`
- `/txs/{hash}/redeemers`

### Address Endpoints (3 tests)
- `/addresses/{address}/transactions`
- `/addresses/{address}/utxos`
- `/addresses/{address}/utxos/{asset}`

### Account Endpoints (6 tests)
- `/accounts/{stake_address}`
- `/accounts/{stake_address}/addresses`
- `/accounts/{stake_address}/delegations`
- `/accounts/{stake_address}/registrations`
- `/accounts/{stake_address}/rewards`

### Asset Endpoints (3 tests)
- `/assets/{asset}`
- `/assets/{asset}/transactions`
- `/assets/{asset}/addresses`

### Pool Endpoints (3 tests)
- `/pools/extended`
- `/pools/{pool_id}/delegators`
- `/pools/{pool_id}/history`

### Epoch Endpoints (3 tests)
- `/epochs/{epoch_no}/blocks`
- `/epochs/{epoch_no}/parameters`
- `/epochs/latest/parameters`

### Metadata Endpoints (2 tests)
- `/metadata/txs/labels/{label}`
- `/metadata/txs/labels/{label}/cbor`

### Governance Endpoints (1 test)
- `/governance/dreps/{drep_id}`

### Script Endpoints (1 test)
- `/scripts/datum/{datum_hash}`

### Genesis Endpoints (1 test)
- `/genesis`

## Understanding Test Results

### Success (No Violations)
When APIs return identical data:
```
test_dolos_vs_blockfrost.py::test_network_eras PASSED [100%]
```

### Failure (Violations Found)
When differences are detected:
```
test_dolos_vs_blockfrost.py::test_genesis FAILED [100%]

Endpoint: /genesis
Differences found:
Values Changed:
  root['active_slots_coefficient']: Blockfrost=0.05 vs Dolos=0.050000
Fields in Dolos but not in Blockfrost:
  root['extra_field']
```

### Violation Types

1. **Values Changed**: Same field exists but has different values
2. **Dictionary Item Added**: Field exists in Dolos but not in Blockfrost
3. **Dictionary Item Removed**: Field exists in Blockfrost but not in Dolos
4. **Type Changes**: Same field has different data types

## Output Reports

### violations_report.json
Comprehensive JSON report with:
- Test summary (total, passed, failed)
- List of all violations with details
- Timestamps for each test

### report.html
Visual HTML report with:
- Test execution timeline
- Pass/fail statistics
- Detailed error messages

### report.json
Machine-readable JSON report with:
- Full test results
- Execution times
- Stack traces for failures

## Advanced Features

### Custom API Comparator

The `APIComparator` class provides:
- **Normalization**: Handles type conversions (e.g., "123" → 123)
- **Deep Comparison**: Recursively compares nested structures
- **Detailed Diff**: Uses DeepDiff for comprehensive analysis

### Session Management

Separate session fixtures for:
- **Dolos**: Clean HTTP session
- **Blockfrost**: Session with API key authentication

### Violation Reporter

Custom reporter that:
- Tracks all violations across tests
- Generates summary statistics
- Creates detailed violation reports

## Troubleshooting

### Connection Errors

**Problem**: `ConnectionError: Failed to establish connection`

**Solution**: 
- Ensure Dolos is running on `http://localhost:3000`
- Check firewall settings
- Verify network connectivity

### Authentication Errors

**Problem**: `401 Unauthorized` from Blockfrost

**Solution**:
- Verify your API key is correct
- Ensure you're using the Preview network key
- Check that the key is set in `.env` file

### Timeout Issues

**Problem**: Tests timing out

**Solution**:
- Increase timeout in `pytest.ini`
- Check network latency
- Verify both APIs are responsive

### Import Errors

**Problem**: `ModuleNotFoundError: No module named 'deepdiff'`

**Solution**:
```bash
pip install -r requirements.txt
```

## Best Practices

1. **Run regularly**: Execute tests after any API updates
2. **Review violations**: Don't ignore differences, investigate them
3. **Update tests**: Keep tests in sync with API changes
4. **Use CI/CD**: Integrate into your pipeline
5. **Monitor trends**: Track violation patterns over time

## CI/CD Integration

### GitHub Actions Example

```yaml
name: API Comparison Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v2
    
    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: '3.9'
    
    - name: Install dependencies
      run: pip install -r requirements.txt
    
    - name: Run Dolos
      run: docker run -d -p 3000:3000 dolos:latest
    
    - name: Run tests
      env:
        BLOCKFROST_API_KEY: ${{ secrets.BLOCKFROST_API_KEY }}
      run: pytest test_dolos_vs_blockfrost.py -v
    
    - name: Upload reports
      if: always()
      uses: actions/upload-artifact@v2
      with:
        name: test-reports
        path: |
          report.html
          violations_report.json
```

## Contributing

To add new endpoint tests:

1. Add the endpoint to the spreadsheet
2. Create a new test function following the pattern:
```python
def test_your_endpoint(dolos_session, blockfrost_session, api_comparator):
    """Test /your/endpoint."""
    endpoint = "/your/endpoint"
    
    dolos_response = dolos_session.get(f"{DOLOS_BASE_URL}{endpoint}")
    blockfrost_response = blockfrost_session.get(f"{BLOCKFROST_BASE_URL}{endpoint}")
    
    assert dolos_response.status_code == 200
    assert blockfrost_response.status_code == 200
    
    is_identical, violations = api_comparator.compare_responses(
        dolos_response.json(),
        blockfrost_response.json(),
        endpoint
    )
    
    if not is_identical:
        pytest.fail("\n".join(violations))
```
