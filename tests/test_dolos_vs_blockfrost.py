"""
Test suite for comparing Dolos API and Blockfrost API endpoints.

This module tests each endpoint from the spreadsheet by:
1. Calling the Dolos API
2. Calling the corresponding Blockfrost API
3. Comparing the JSON responses
4. Reporting any data violations
"""

import pytest
import requests
from typing import Dict, List, Any, Tuple
from deepdiff import DeepDiff
import json
import os
from dotenv import load_dotenv


# Configuration
load_dotenv()

DOLOS_BASE_URL = os.getenv("DOLOS_BASE_URL")
BLOCKFROST_BASE_URL = os.getenv("BLOCKFROST_BASE_URL")
BLOCKFROST_API_KEY = os.getenv("BLOCKFROST_API_KEY")


class APIComparator:
    """Helper class for comparing API responses."""

    @staticmethod
    def normalize_response(data: Any) -> Any:
        """
        Normalize response data for comparison.
        Handles type conversions and formatting differences.
        """
        if isinstance(data, dict):
            return {
                k: APIComparator.normalize_response(v)
                for k, v in data.items()
            }
        elif isinstance(data, list):
            return [APIComparator.normalize_response(item) for item in data]
        elif isinstance(data, str):
            # Try to convert string numbers to actual numbers for comparison
            try:
                if '.' in data:
                    return float(data)
                return int(data)
            except (ValueError, TypeError):
                return data
        return data

    @staticmethod
    def compare_responses(
        dolos_response: Dict,
        blockfrost_response: Dict,
        endpoint: str
    ) -> Tuple[bool, List[str]]:
        """
        Compare two API responses and return violations.

        Returns:
            Tuple of (is_identical, list_of_violations)
        """
        violations = []

        # Normalize responses for comparison
        dolos_normalized = APIComparator.normalize_response(
            dolos_response
        )
        blockfrost_normalized = APIComparator.normalize_response(
            blockfrost_response
        )

        # Use DeepDiff for comprehensive comparison
        diff = DeepDiff(
            blockfrost_normalized,
            dolos_normalized,
            ignore_order=False,
            verbose_level=2
        )

        if diff:
            violations.append(f"Endpoint: {endpoint}")
            violations.append(
                f"Differences found: "
                f"{json.dumps(diff, indent=2, default=str)}"
            )

            # Parse specific violation types
            if 'values_changed' in diff:
                violations.append("\nValues Changed:")
                for path, change in diff['values_changed'].items():
                    violations.append(
                        f"  {path}: Blockfrost={change['old_value']} "
                        f"vs Dolos={change['new_value']}"
                    )

            if 'dictionary_item_added' in diff:
                violations.append("\nFields in Dolos but not in Blockfrost:")
                for item in diff['dictionary_item_added']:
                    violations.append(f"  {item}")

            if 'dictionary_item_removed' in diff:
                violations.append("\nFields in Blockfrost but not in Dolos:")
                for item in diff['dictionary_item_removed']:
                    violations.append(f"  {item}")

            if 'type_changes' in diff:
                violations.append("\nType Changes:")
                for path, change in diff['type_changes'].items():
                    violations.append(
                        f"  {path}: Blockfrost type={change['old_type']} "
                        f"vs Dolos type={change['new_type']}"
                    )

            return False, violations

        return True, []


@pytest.fixture
def api_comparator():
    """Fixture providing the API comparator instance."""
    return APIComparator()


@pytest.fixture
def dolos_session():
    """Fixture providing a requests session for Dolos API."""
    session = requests.Session()
    session.headers.update({"Content-Type": "application/json"})
    return session


@pytest.fixture
def blockfrost_session():
    """Fixture providing a requests session for Blockfrost API."""
    session = requests.Session()
    session.headers.update({
        "Content-Type": "application/json",
        "project_id": BLOCKFROST_API_KEY
    })
    return session


# Test cases for each endpoint from the spreadsheet

def test_network_eras(dolos_session, blockfrost_session, api_comparator):
    """Test /network/eras endpoint."""
    endpoint = "/network/eras"

    dolos_response = dolos_session.get(f"{DOLOS_BASE_URL}{endpoint}")
    blockfrost_response = blockfrost_session.get(
        f"{BLOCKFROST_BASE_URL}{endpoint}"
    )

    assert dolos_response.status_code == 200, (
        f"Dolos API failed: {dolos_response.text}"
    )
    assert blockfrost_response.status_code == 200, (
        f"Blockfrost API failed: {blockfrost_response.text}"
    )

    is_identical, violations = api_comparator.compare_responses(
        dolos_response.json(),
        blockfrost_response.json(),
        endpoint
    )

    if not is_identical:
        pytest.fail("\n".join(violations))


def test_tx_cbor(dolos_session, blockfrost_session, api_comparator):
    """Test /txs/{hash}/cbor endpoint."""
    endpoint = (
        "/txs/b61bc5edddfdc52e46a1476acf41794bdb1e505f601eef721b2721"
        "ebedb72767/cbor"
    )

    dolos_response = dolos_session.get(f"{DOLOS_BASE_URL}{endpoint}")
    blockfrost_response = blockfrost_session.get(
        f"{BLOCKFROST_BASE_URL}{endpoint}"
    )

    assert dolos_response.status_code == 200, (
        f"Dolos API failed: {dolos_response.text}"
    )
    assert blockfrost_response.status_code == 200, (
        f"Blockfrost API failed: {blockfrost_response.text}"
    )

    is_identical, violations = api_comparator.compare_responses(
        dolos_response.json(),
        blockfrost_response.json(),
        endpoint
    )

    if not is_identical:
        pytest.fail("\n".join(violations))


def test_tx_utxos(dolos_session, blockfrost_session, api_comparator):
    """Test /txs/{hash}/utxos endpoint."""
    endpoint = (
        "/txs/068e436fc1e2dc030f59f5ed99efc12b2464e499eb7ed9315fe5731"
        "a3263baf9/utxos"
    )

    dolos_response = dolos_session.get(f"{DOLOS_BASE_URL}{endpoint}")
    blockfrost_response = blockfrost_session.get(
        f"{BLOCKFROST_BASE_URL}{endpoint}"
    )

    assert dolos_response.status_code == 200, (
        f"Dolos API failed: {dolos_response.text}"
    )
    assert blockfrost_response.status_code == 200, (
        f"Blockfrost API failed: {blockfrost_response.text}"
    )

    is_identical, violations = api_comparator.compare_responses(
        dolos_response.json(),
        blockfrost_response.json(),
        endpoint
    )

    if not is_identical:
        pytest.fail("\n".join(violations))


def test_tx_metadata(dolos_session, blockfrost_session, api_comparator):
    """Test /txs/{hash}/metadata endpoint."""
    endpoint = (
        "/txs/b61bc5edddfdc52e46a1476acf41794bdb1e505f601eef721b2721"
        "ebedb72767/metadata"
    )

    dolos_response = dolos_session.get(f"{DOLOS_BASE_URL}{endpoint}")
    blockfrost_response = blockfrost_session.get(
        f"{BLOCKFROST_BASE_URL}{endpoint}"
    )

    assert dolos_response.status_code == 200, (
        f"Dolos API failed: {dolos_response.text}"
    )
    assert blockfrost_response.status_code == 200, (
        f"Blockfrost API failed: {blockfrost_response.text}"
    )

    is_identical, violations = api_comparator.compare_responses(
        dolos_response.json(),
        blockfrost_response.json(),
        endpoint
    )

    if not is_identical:
        pytest.fail("\n".join(violations))


def test_blocks_next(dolos_session, blockfrost_session, api_comparator):
    """Test /blocks/{block_id}/next endpoint."""
    endpoint = "/blocks/10000/next"

    dolos_response = dolos_session.get(f"{DOLOS_BASE_URL}{endpoint}")
    blockfrost_response = blockfrost_session.get(
        f"{BLOCKFROST_BASE_URL}{endpoint}"
    )

    assert dolos_response.status_code == 200, (
        f"Dolos API failed: {dolos_response.text}"
    )
    assert blockfrost_response.status_code == 200, (
        f"Blockfrost API failed: {blockfrost_response.text}"
    )

    is_identical, violations = api_comparator.compare_responses(
        dolos_response.json(),
        blockfrost_response.json(),
        endpoint
    )

    if not is_identical:
        pytest.fail("\n".join(violations))


def test_blocks_previous(dolos_session, blockfrost_session, api_comparator):
    """Test /blocks/{block_id}/previous endpoint."""
    endpoint = "/blocks/10000/previous"

    dolos_response = dolos_session.get(f"{DOLOS_BASE_URL}{endpoint}")
    blockfrost_response = blockfrost_session.get(
        f"{BLOCKFROST_BASE_URL}{endpoint}"
    )

    assert dolos_response.status_code == 200, (
        f"Dolos API failed: {dolos_response.text}"
    )
    assert blockfrost_response.status_code == 200, (
        f"Blockfrost API failed: {blockfrost_response.text}"
    )

    is_identical, violations = api_comparator.compare_responses(
        dolos_response.json(),
        blockfrost_response.json(),
        endpoint
    )

    if not is_identical:
        pytest.fail("\n".join(violations))


def test_blocks_txs(dolos_session, blockfrost_session, api_comparator):
    """Test /blocks/{block_id}/txs endpoint."""
    endpoint = "/blocks/300000/txs"

    dolos_response = dolos_session.get(f"{DOLOS_BASE_URL}{endpoint}")
    blockfrost_response = blockfrost_session.get(
        f"{BLOCKFROST_BASE_URL}{endpoint}"
    )

    assert dolos_response.status_code == 200, (
        f"Dolos API failed: {dolos_response.text}"
    )
    assert blockfrost_response.status_code == 200, (
        f"Blockfrost API failed: {blockfrost_response.text}"
    )

    is_identical, violations = api_comparator.compare_responses(
        dolos_response.json(),
        blockfrost_response.json(),
        endpoint
    )

    if not is_identical:
        pytest.fail("\n".join(violations))


def test_blocks_latest_txs(dolos_session, blockfrost_session, api_comparator):
    """Test /blocks/latest/txs endpoint."""
    endpoint = "/blocks/latest/txs"

    dolos_response = dolos_session.get(f"{DOLOS_BASE_URL}{endpoint}")
    blockfrost_response = blockfrost_session.get(
        f"{BLOCKFROST_BASE_URL}{endpoint}"
    )

    assert dolos_response.status_code == 200, (
        f"Dolos API failed: {dolos_response.text}"
    )
    assert blockfrost_response.status_code == 200, (
        f"Blockfrost API failed: {blockfrost_response.text}"
    )

    is_identical, violations = api_comparator.compare_responses(
        dolos_response.json(),
        blockfrost_response.json(),
        endpoint
    )

    if not is_identical:
        pytest.fail("\n".join(violations))


def test_blocks_slot(dolos_session, blockfrost_session, api_comparator):
    """Test /blocks/slot/{slot_number} endpoint."""
    endpoint = "/blocks/slot/87910204"

    dolos_response = dolos_session.get(f"{DOLOS_BASE_URL}{endpoint}")
    blockfrost_response = blockfrost_session.get(
        f"{BLOCKFROST_BASE_URL}{endpoint}"
    )

    assert dolos_response.status_code == 200, (
        f"Dolos API failed: {dolos_response.text}"
    )
    assert blockfrost_response.status_code == 200, (
        f"Blockfrost API failed: {blockfrost_response.text}"
    )

    is_identical, violations = api_comparator.compare_responses(
        dolos_response.json(),
        blockfrost_response.json(),
        endpoint
    )

    if not is_identical:
        pytest.fail("\n".join(violations))


def test_genesis(dolos_session, blockfrost_session, api_comparator):
    """Test /genesis endpoint."""
    endpoint = "/genesis"

    dolos_response = dolos_session.get(f"{DOLOS_BASE_URL}{endpoint}")
    blockfrost_response = blockfrost_session.get(
        f"{BLOCKFROST_BASE_URL}{endpoint}"
    )

    assert dolos_response.status_code == 200, (
        f"Dolos API failed: {dolos_response.text}"
    )
    assert blockfrost_response.status_code == 200, (
        f"Blockfrost API failed: {blockfrost_response.text}"
    )

    is_identical, violations = api_comparator.compare_responses(
        dolos_response.json(),
        blockfrost_response.json(),
        endpoint
    )

    if not is_identical:
        pytest.fail("\n".join(violations))


def test_address_transactions(
    dolos_session, blockfrost_session, api_comparator
):
    """Test /addresses/{address}/transactions endpoint."""
    endpoint = (
        "/addresses/addr_test1wq05sks3ky00gy54vtv98z5skqpezpp4l50xtu"
        "sepnydpyspemt6h/transactions"
    )

    dolos_response = dolos_session.get(f"{DOLOS_BASE_URL}{endpoint}")
    blockfrost_response = blockfrost_session.get(
        f"{BLOCKFROST_BASE_URL}{endpoint}"
    )

    assert dolos_response.status_code == 200, (
        f"Dolos API failed: {dolos_response.text}"
    )
    assert blockfrost_response.status_code == 200, (
        f"Blockfrost API failed: {blockfrost_response.text}"
    )

    is_identical, violations = api_comparator.compare_responses(
        dolos_response.json(),
        blockfrost_response.json(),
        endpoint
    )

    if not is_identical:
        pytest.fail("\n".join(violations))


def test_tx_mirs(dolos_session, blockfrost_session, api_comparator):
    """Test /txs/{hash}/mirs endpoint."""
    endpoint = (
        "/txs/08adb9d083be3c080ae884ace766a74683c9820a4b8940cc45fb7c"
        "5a041f9c04/mirs"
    )

    dolos_response = dolos_session.get(f"{DOLOS_BASE_URL}{endpoint}")
    blockfrost_response = blockfrost_session.get(
        f"{BLOCKFROST_BASE_URL}{endpoint}"
    )

    assert dolos_response.status_code == 200, (
        f"Dolos API failed: {dolos_response.text}"
    )
    assert blockfrost_response.status_code == 200, (
        f"Blockfrost API failed: {blockfrost_response.text}"
    )

    is_identical, violations = api_comparator.compare_responses(
        dolos_response.json(),
        blockfrost_response.json(),
        endpoint
    )

    if not is_identical:
        pytest.fail("\n".join(violations))


def test_tx_withdrawals(dolos_session, blockfrost_session, api_comparator):
    """Test /txs/{hash}/withdrawals endpoint."""
    endpoint = (
        "/txs/5d438ccecf62ad384ec1e75c5ff0ed60217c37fd6cfefd1625622e"
        "3bf8e8a71b/withdrawals"
    )

    dolos_response = dolos_session.get(f"{DOLOS_BASE_URL}{endpoint}")
    blockfrost_response = blockfrost_session.get(
        f"{BLOCKFROST_BASE_URL}{endpoint}"
    )

    assert dolos_response.status_code == 200, (
        f"Dolos API failed: {dolos_response.text}"
    )
    assert blockfrost_response.status_code == 200, (
        f"Blockfrost API failed: {blockfrost_response.text}"
    )

    is_identical, violations = api_comparator.compare_responses(
        dolos_response.json(),
        blockfrost_response.json(),
        endpoint
    )

    if not is_identical:
        pytest.fail("\n".join(violations))


def test_tx_delegations(dolos_session, blockfrost_session, api_comparator):
    """Test /txs/{hash}/delegations endpoint."""
    endpoint = (
        "/txs/6091f714ccbb720fcb7db72fad984afe94095f7a5aa9a03879b60f"
        "bc35740a97/delegations"
    )

    dolos_response = dolos_session.get(f"{DOLOS_BASE_URL}{endpoint}")
    blockfrost_response = blockfrost_session.get(
        f"{BLOCKFROST_BASE_URL}{endpoint}"
    )

    assert dolos_response.status_code == 200, (
        f"Dolos API failed: {dolos_response.text}"
    )
    assert blockfrost_response.status_code == 200, (
        f"Blockfrost API failed: {blockfrost_response.text}"
    )

    is_identical, violations = api_comparator.compare_responses(
        dolos_response.json(),
        blockfrost_response.json(),
        endpoint
    )

    if not is_identical:
        pytest.fail("\n".join(violations))


def test_tx_stakes(dolos_session, blockfrost_session, api_comparator):
    """Test /txs/{hash}/stakes endpoint."""
    endpoint = (
        "/txs/e3ca57e8f323265742a8f4e79ff9af884c9ff8719bd4f7788adaea"
        "4c33ba07b6/stakes"
    )

    dolos_response = dolos_session.get(f"{DOLOS_BASE_URL}{endpoint}")
    blockfrost_response = blockfrost_session.get(
        f"{BLOCKFROST_BASE_URL}{endpoint}"
    )

    assert dolos_response.status_code == 200, (
        f"Dolos API failed: {dolos_response.text}"
    )
    assert blockfrost_response.status_code == 200, (
        f"Blockfrost API failed: {blockfrost_response.text}"
    )

    is_identical, violations = api_comparator.compare_responses(
        dolos_response.json(),
        blockfrost_response.json(),
        endpoint
    )

    if not is_identical:
        pytest.fail("\n".join(violations))


def test_tx_info(dolos_session, blockfrost_session, api_comparator):
    """Test /txs/{hash} endpoint."""
    endpoint = (
        "/txs/421f66ebac7dca3551b7936d62e26f85cdc13591ed4aa86cacbbe1"
        "a0f0da32e5"
    )

    dolos_response = dolos_session.get(f"{DOLOS_BASE_URL}{endpoint}")
    blockfrost_response = blockfrost_session.get(
        f"{BLOCKFROST_BASE_URL}{endpoint}"
    )

    assert dolos_response.status_code == 200, (
        f"Dolos API failed: {dolos_response.text}"
    )
    assert blockfrost_response.status_code == 200, (
        f"Blockfrost API failed: {blockfrost_response.text}"
    )

    is_identical, violations = api_comparator.compare_responses(
        dolos_response.json(),
        blockfrost_response.json(),
        endpoint
    )

    if not is_identical:
        pytest.fail("\n".join(violations))


def test_tx_metadata_cbor(
    dolos_session, blockfrost_session, api_comparator
):
    """Test /txs/{hash}/metadata/cbor endpoint."""
    endpoint = (
        "/txs/b61bc5edddfdc52e46a1476acf41794bdb1e505f601eef721b2721"
        "ebedb72767/metadata/cbor"
    )

    dolos_response = dolos_session.get(f"{DOLOS_BASE_URL}{endpoint}")
    blockfrost_response = blockfrost_session.get(
        f"{BLOCKFROST_BASE_URL}{endpoint}"
    )

    assert dolos_response.status_code == 200, (
        f"Dolos API failed: {dolos_response.text}"
    )
    assert blockfrost_response.status_code == 200, (
        f"Blockfrost API failed: {blockfrost_response.text}"
    )

    is_identical, violations = api_comparator.compare_responses(
        dolos_response.json(),
        blockfrost_response.json(),
        endpoint
    )

    if not is_identical:
        pytest.fail("\n".join(violations))


def test_blocks_latest(dolos_session, blockfrost_session, api_comparator):
    """Test /blocks/latest endpoint."""
    endpoint = "/blocks/latest"

    dolos_response = dolos_session.get(f"{DOLOS_BASE_URL}{endpoint}")
    blockfrost_response = blockfrost_session.get(
        f"{BLOCKFROST_BASE_URL}{endpoint}"
    )

    assert dolos_response.status_code == 200, (
        f"Dolos API failed: {dolos_response.text}"
    )
    assert blockfrost_response.status_code == 200, (
        f"Blockfrost API failed: {blockfrost_response.text}"
    )

    is_identical, violations = api_comparator.compare_responses(
        dolos_response.json(),
        blockfrost_response.json(),
        endpoint
    )

    if not is_identical:
        pytest.fail("\n".join(violations))


def test_account_addresses(
    dolos_session, blockfrost_session, api_comparator
):
    """Test /accounts/{stake_address}/addresses endpoint."""
    endpoint = (
        "/accounts/stake_test1up8590900edfw9qxjmzfxa4jsd992jgj0tvgv3z"
        "md6cvz8cpkrg6h/addresses"
    )

    dolos_response = dolos_session.get(f"{DOLOS_BASE_URL}{endpoint}")
    blockfrost_response = blockfrost_session.get(
        f"{BLOCKFROST_BASE_URL}{endpoint}"
    )

    assert dolos_response.status_code == 200, (
        f"Dolos API failed: {dolos_response.text}"
    )
    assert blockfrost_response.status_code == 200, (
        f"Blockfrost API failed: {blockfrost_response.text}"
    )

    is_identical, violations = api_comparator.compare_responses(
        dolos_response.json(),
        blockfrost_response.json(),
        endpoint
    )

    if not is_identical:
        pytest.fail("\n".join(violations))


def test_account_delegations(
    dolos_session, blockfrost_session, api_comparator
):
    """Test /accounts/{stake_address}/delegations endpoint."""
    endpoint = (
        "/accounts/stake_test1up8590900edfw9qxjmzfxa4jsd992jgj0tvgv3z"
        "md6cvz8cpkrg6h/delegations"
    )

    dolos_response = dolos_session.get(f"{DOLOS_BASE_URL}{endpoint}")
    blockfrost_response = blockfrost_session.get(
        f"{BLOCKFROST_BASE_URL}{endpoint}"
    )

    assert dolos_response.status_code == 200, (
        f"Dolos API failed: {dolos_response.text}"
    )
    assert blockfrost_response.status_code == 200, (
        f"Blockfrost API failed: {blockfrost_response.text}"
    )

    is_identical, violations = api_comparator.compare_responses(
        dolos_response.json(),
        blockfrost_response.json(),
        endpoint
    )

    if not is_identical:
        pytest.fail("\n".join(violations))


def test_account_registrations(
    dolos_session, blockfrost_session, api_comparator
):
    """Test /accounts/{stake_address}/registrations endpoint."""
    endpoint = (
        "/accounts/stake_test1up8590900edfw9qxjmzfxa4jsd992jgj0tvgv3z"
        "md6cvz8cpkrg6h/registrations"
    )

    dolos_response = dolos_session.get(f"{DOLOS_BASE_URL}{endpoint}")
    blockfrost_response = blockfrost_session.get(
        f"{BLOCKFROST_BASE_URL}{endpoint}"
    )

    assert dolos_response.status_code == 200, (
        f"Dolos API failed: {dolos_response.text}"
    )
    assert blockfrost_response.status_code == 200, (
        f"Blockfrost API failed: {blockfrost_response.text}"
    )

    is_identical, violations = api_comparator.compare_responses(
        dolos_response.json(),
        blockfrost_response.json(),
        endpoint
    )

    if not is_identical:
        pytest.fail("\n".join(violations))


def test_asset_info(dolos_session, blockfrost_session, api_comparator):
    """Test /assets/{asset} endpoint."""
    endpoint = (
        "/assets/408e22449de761a35f54dd708cc8273e5dd706179b8e2a67a81b6"
        "e95416c657854657374546f6b656e"
    )

    dolos_response = dolos_session.get(f"{DOLOS_BASE_URL}{endpoint}")
    blockfrost_response = blockfrost_session.get(
        f"{BLOCKFROST_BASE_URL}{endpoint}"
    )

    assert dolos_response.status_code == 200, (
        f"Dolos API failed: {dolos_response.text}"
    )
    assert blockfrost_response.status_code == 200, (
        f"Blockfrost API failed: {blockfrost_response.text}"
    )

    is_identical, violations = api_comparator.compare_responses(
        dolos_response.json(),
        blockfrost_response.json(),
        endpoint
    )

    if not is_identical:
        pytest.fail("\n".join(violations))


def test_address_utxos(dolos_session, blockfrost_session, api_comparator):
    """Test /addresses/{address}/utxos endpoint."""
    endpoint = (
        "/addresses/addr_test1wzzctdyf9nkgrzqw6vxhaq8mpla7zhzjyjmk6tx"
        "yu0wsgrgek9nj3/utxos"
    )

    dolos_response = dolos_session.get(f"{DOLOS_BASE_URL}{endpoint}")
    blockfrost_response = blockfrost_session.get(
        f"{BLOCKFROST_BASE_URL}{endpoint}"
    )

    assert dolos_response.status_code == 200, (
        f"Dolos API failed: {dolos_response.text}"
    )
    assert blockfrost_response.status_code == 200, (
        f"Blockfrost API failed: {blockfrost_response.text}"
    )

    is_identical, violations = api_comparator.compare_responses(
        dolos_response.json(),
        blockfrost_response.json(),
        endpoint
    )

    if not is_identical:
        pytest.fail("\n".join(violations))


def test_tx_pool_retires(dolos_session, blockfrost_session, api_comparator):
    """Test /txs/{hash}/pool_retires endpoint."""
    endpoint = (
        "/txs/08adb9d083be3c080ae884ace766a74683c9820a4b8940cc45fb7c"
        "5a041f9c04/pool_retires"
    )

    dolos_response = dolos_session.get(f"{DOLOS_BASE_URL}{endpoint}")
    blockfrost_response = blockfrost_session.get(
        f"{BLOCKFROST_BASE_URL}{endpoint}"
    )

    assert dolos_response.status_code == 200, (
        f"Dolos API failed: {dolos_response.text}"
    )
    assert blockfrost_response.status_code == 200, (
        f"Blockfrost API failed: {blockfrost_response.text}"
    )

    is_identical, violations = api_comparator.compare_responses(
        dolos_response.json(),
        blockfrost_response.json(),
        endpoint
    )

    if not is_identical:
        pytest.fail("\n".join(violations))


def test_tx_pool_updates(dolos_session, blockfrost_session, api_comparator):
    """Test /txs/{hash}/pool_updates endpoint."""
    endpoint = (
        "/txs/6091f714ccbb720fcb7db72fad984afe94095f7a5aa9a03879b60f"
        "bc35740a97/pool_updates"
    )

    dolos_response = dolos_session.get(f"{DOLOS_BASE_URL}{endpoint}")
    blockfrost_response = blockfrost_session.get(
        f"{BLOCKFROST_BASE_URL}{endpoint}"
    )

    assert dolos_response.status_code == 200, (
        f"Dolos API failed: {dolos_response.text}"
    )
    assert blockfrost_response.status_code == 200, (
        f"Blockfrost API failed: {blockfrost_response.text}"
    )

    is_identical, violations = api_comparator.compare_responses(
        dolos_response.json(),
        blockfrost_response.json(),
        endpoint
    )

    if not is_identical:
        pytest.fail("\n".join(violations))


def test_account_info(dolos_session, blockfrost_session, api_comparator):
    """Test /accounts/{stake_address} endpoint."""
    endpoint = (
        "/accounts/stake_test1up8590900edfw9qxjmzfxa4jsd992jgj0tvgv3z"
        "md6cvz8cpkrg6h"
    )

    dolos_response = dolos_session.get(f"{DOLOS_BASE_URL}{endpoint}")
    blockfrost_response = blockfrost_session.get(
        f"{BLOCKFROST_BASE_URL}{endpoint}"
    )

    assert dolos_response.status_code == 200, (
        f"Dolos API failed: {dolos_response.text}"
    )
    assert blockfrost_response.status_code == 200, (
        f"Blockfrost API failed: {blockfrost_response.text}"
    )

    is_identical, violations = api_comparator.compare_responses(
        dolos_response.json(),
        blockfrost_response.json(),
        endpoint
    )

    if not is_identical:
        pytest.fail("\n".join(violations))


def test_address_utxo_by_asset(
    dolos_session, blockfrost_session, api_comparator
):
    """Test /addresses/{address}/utxos/{asset} endpoint."""
    endpoint = (
        "/addresses/addr_test1wzzctdyf9nkgrzqw6vxhaq8mpla7zhzjyjmk6tx"
        "yu0wsgrgek9nj3/utxos/f0ff48bbb7bbe9d59a40f1ce90e9e9d0ff5002"
        "ec48f232b49ca0fb9a000643b0796f75725f68616e646c65"
    )

    dolos_response = dolos_session.get(f"{DOLOS_BASE_URL}{endpoint}")
    blockfrost_response = blockfrost_session.get(
        f"{BLOCKFROST_BASE_URL}{endpoint}"
    )

    assert dolos_response.status_code == 200, (
        f"Dolos API failed: {dolos_response.text}"
    )
    assert blockfrost_response.status_code == 200, (
        f"Blockfrost API failed: {blockfrost_response.text}"
    )

    is_identical, violations = api_comparator.compare_responses(
        dolos_response.json(),
        blockfrost_response.json(),
        endpoint
    )

    if not is_identical:
        pytest.fail("\n".join(violations))


def test_epoch_parameters(dolos_session, blockfrost_session, api_comparator):
    """Test /epochs/{epoch_no}/parameters endpoint."""
    endpoint = "/epochs/1108/parameters"

    dolos_response = dolos_session.get(f"{DOLOS_BASE_URL}{endpoint}")
    blockfrost_response = blockfrost_session.get(
        f"{BLOCKFROST_BASE_URL}{endpoint}"
    )

    assert dolos_response.status_code == 200, (
        f"Dolos API failed: {dolos_response.text}"
    )
    assert blockfrost_response.status_code == 200, (
        f"Blockfrost API failed: {blockfrost_response.text}"
    )

    is_identical, violations = api_comparator.compare_responses(
        dolos_response.json(),
        blockfrost_response.json(),
        endpoint
    )

    if not is_identical:
        pytest.fail("\n".join(violations))


def test_epoch_latest_parameters(
    dolos_session, blockfrost_session, api_comparator
):
    """Test /epochs/latest/parameters endpoint."""
    endpoint = "/epochs/latest/parameters"

    dolos_response = dolos_session.get(f"{DOLOS_BASE_URL}{endpoint}")
    blockfrost_response = blockfrost_session.get(
        f"{BLOCKFROST_BASE_URL}{endpoint}"
    )

    assert dolos_response.status_code == 200, (
        f"Dolos API failed: {dolos_response.text}"
    )
    assert blockfrost_response.status_code == 200, (
        f"Blockfrost API failed: {blockfrost_response.text}"
    )

    is_identical, violations = api_comparator.compare_responses(
        dolos_response.json(),
        blockfrost_response.json(),
        endpoint
    )

    if not is_identical:
        pytest.fail("\n".join(violations))


def test_tx_redeemers(dolos_session, blockfrost_session, api_comparator):
    """Test /txs/{hash}/redeemers endpoint."""
    endpoint = (
        "/txs/08adb9d083be3c080ae884ace766a74683c9820a4b8940cc45fb7c"
        "5a041f9c04/redeemers"
    )

    dolos_response = dolos_session.get(f"{DOLOS_BASE_URL}{endpoint}")
    blockfrost_response = blockfrost_session.get(
        f"{BLOCKFROST_BASE_URL}{endpoint}"
    )

    assert dolos_response.status_code == 200, (
        f"Dolos API failed: {dolos_response.text}"
    )
    assert blockfrost_response.status_code == 200, (
        f"Blockfrost API failed: {blockfrost_response.text}"
    )

    is_identical, violations = api_comparator.compare_responses(
        dolos_response.json(),
        blockfrost_response.json(),
        endpoint
    )

    if not is_identical:
        pytest.fail("\n".join(violations))


def test_metadata_txs_labels_cbor(
    dolos_session, blockfrost_session, api_comparator
):
    """Test /metadata/txs/labels/{label}/cbor endpoint."""
    endpoint = "/metadata/txs/labels/1226/cbor"

    dolos_response = dolos_session.get(f"{DOLOS_BASE_URL}{endpoint}")
    blockfrost_response = blockfrost_session.get(
        f"{BLOCKFROST_BASE_URL}{endpoint}"
    )

    assert dolos_response.status_code == 200, (
        f"Dolos API failed: {dolos_response.text}"
    )
    assert blockfrost_response.status_code == 200, (
        f"Blockfrost API failed: {blockfrost_response.text}"
    )

    is_identical, violations = api_comparator.compare_responses(
        dolos_response.json(),
        blockfrost_response.json(),
        endpoint
    )

    if not is_identical:
        pytest.fail("\n".join(violations))


def test_metadata_txs_labels(
    dolos_session, blockfrost_session, api_comparator
):
    """Test /metadata/txs/labels/{label} endpoint."""
    endpoint = "/metadata/txs/labels/1226"

    dolos_response = dolos_session.get(f"{DOLOS_BASE_URL}{endpoint}")
    blockfrost_response = blockfrost_session.get(
        f"{BLOCKFROST_BASE_URL}{endpoint}"
    )

    assert dolos_response.status_code == 200, (
        f"Dolos API failed: {dolos_response.text}"
    )
    assert blockfrost_response.status_code == 200, (
        f"Blockfrost API failed: {blockfrost_response.text}"
    )

    is_identical, violations = api_comparator.compare_responses(
        dolos_response.json(),
        blockfrost_response.json(),
        endpoint
    )

    if not is_identical:
        pytest.fail("\n".join(violations))


def test_pool_delegators(dolos_session, blockfrost_session, api_comparator):
    """Test /pools/{pool_id}/delegators endpoint."""
    endpoint = (
        "/pools/pool1elet8uart9cuw3lmntqhfn2f44rf52dg6v5ppzkcysxx2"
        "68s43n/delegators"
    )

    dolos_response = dolos_session.get(f"{DOLOS_BASE_URL}{endpoint}")
    blockfrost_response = blockfrost_session.get(
        f"{BLOCKFROST_BASE_URL}{endpoint}"
    )

    assert dolos_response.status_code == 200, (
        f"Dolos API failed: {dolos_response.text}"
    )
    assert blockfrost_response.status_code == 200, (
        f"Blockfrost API failed: {blockfrost_response.text}"
    )

    is_identical, violations = api_comparator.compare_responses(
        dolos_response.json(),
        blockfrost_response.json(),
        endpoint
    )

    if not is_identical:
        pytest.fail("\n".join(violations))


def test_epoch_blocks(dolos_session, blockfrost_session, api_comparator):
    """Test /epochs/{epoch_no}/blocks endpoint."""
    endpoint = "/epochs/1079/blocks"

    dolos_response = dolos_session.get(f"{DOLOS_BASE_URL}{endpoint}")
    blockfrost_response = blockfrost_session.get(
        f"{BLOCKFROST_BASE_URL}{endpoint}"
    )

    assert dolos_response.status_code == 200, (
        f"Dolos API failed: {dolos_response.text}"
    )
    assert blockfrost_response.status_code == 200, (
        f"Blockfrost API failed: {blockfrost_response.text}"
    )

    is_identical, violations = api_comparator.compare_responses(
        dolos_response.json(),
        blockfrost_response.json(),
        endpoint
    )

    if not is_identical:
        pytest.fail("\n".join(violations))


def test_asset_transactions(
    dolos_session, blockfrost_session, api_comparator
):
    """Test /assets/{asset}/transactions endpoint."""
    endpoint = (
        "/assets/408e22449de761a35f54dd708cc8273e5dd706179b8e2a67a81b6"
        "e95416c657854657374546f6b656e/transactions"
    )

    dolos_response = dolos_session.get(f"{DOLOS_BASE_URL}{endpoint}")
    blockfrost_response = blockfrost_session.get(
        f"{BLOCKFROST_BASE_URL}{endpoint}"
    )

    assert dolos_response.status_code == 200, (
        f"Dolos API failed: {dolos_response.text}"
    )
    assert blockfrost_response.status_code == 200, (
        f"Blockfrost API failed: {blockfrost_response.text}"
    )

    is_identical, violations = api_comparator.compare_responses(
        dolos_response.json(),
        blockfrost_response.json(),
        endpoint
    )

    if not is_identical:
        pytest.fail("\n".join(violations))


def test_asset_addresses(dolos_session, blockfrost_session, api_comparator):
    """Test /assets/{asset}/addresses endpoint."""
    endpoint = (
        "/assets/408e22449de761a35f54dd708cc8273e5dd706179b8e2a67a81b6"
        "e95416c657854657374546f6b656e/addresses"
    )

    dolos_response = dolos_session.get(f"{DOLOS_BASE_URL}{endpoint}")
    blockfrost_response = blockfrost_session.get(
        f"{BLOCKFROST_BASE_URL}{endpoint}"
    )

    assert dolos_response.status_code == 200, (
        f"Dolos API failed: {dolos_response.text}"
    )
    assert blockfrost_response.status_code == 200, (
        f"Blockfrost API failed: {blockfrost_response.text}"
    )

    is_identical, violations = api_comparator.compare_responses(
        dolos_response.json(),
        blockfrost_response.json(),
        endpoint
    )

    if not is_identical:
        pytest.fail("\n".join(violations))


def test_block_by_hash(dolos_session, blockfrost_session, api_comparator):
    """Test /blocks/{hash_or_number} endpoint."""
    endpoint = (
        "/blocks/2c100d30b63b567a5ba5fe4fcc1632a6644ff06e400d89d9eecdb"
        "1631773d16a"
    )

    dolos_response = dolos_session.get(f"{DOLOS_BASE_URL}{endpoint}")
    blockfrost_response = blockfrost_session.get(
        f"{BLOCKFROST_BASE_URL}{endpoint}"
    )

    assert dolos_response.status_code == 200, (
        f"Dolos API failed: {dolos_response.text}"
    )
    assert blockfrost_response.status_code == 200, (
        f"Blockfrost API failed: {blockfrost_response.text}"
    )

    is_identical, violations = api_comparator.compare_responses(
        dolos_response.json(),
        blockfrost_response.json(),
        endpoint
    )

    if not is_identical:
        pytest.fail("\n".join(violations))


def test_governance_dreps(
    dolos_session, blockfrost_session, api_comparator
):
    """Test /governance/dreps/{drep_id} endpoint."""
    endpoint = (
        "/governance/dreps/drep1yfqtxkcyycq5lsvllu8ue9m40qlelsuq5zaws"
        "2khpnnd05ccww9xy"
    )

    dolos_response = dolos_session.get(f"{DOLOS_BASE_URL}{endpoint}")
    blockfrost_response = blockfrost_session.get(
        f"{BLOCKFROST_BASE_URL}{endpoint}"
    )

    assert dolos_response.status_code == 200, (
        f"Dolos API failed: {dolos_response.text}"
    )
    assert blockfrost_response.status_code == 200, (
        f"Blockfrost API failed: {blockfrost_response.text}"
    )

    is_identical, violations = api_comparator.compare_responses(
        dolos_response.json(),
        blockfrost_response.json(),
        endpoint
    )

    if not is_identical:
        pytest.fail("\n".join(violations))


def test_network(dolos_session, blockfrost_session, api_comparator):
    """Test /network endpoint."""
    endpoint = "/network"

    dolos_response = dolos_session.get(f"{DOLOS_BASE_URL}{endpoint}")
    blockfrost_response = blockfrost_session.get(
        f"{BLOCKFROST_BASE_URL}{endpoint}"
    )

    assert dolos_response.status_code == 200, (
        f"Dolos API failed: {dolos_response.text}"
    )
    assert blockfrost_response.status_code == 200, (
        f"Blockfrost API failed: {blockfrost_response.text}"
    )

    is_identical, violations = api_comparator.compare_responses(
        dolos_response.json(),
        blockfrost_response.json(),
        endpoint
    )

    if not is_identical:
        pytest.fail("\n".join(violations))


def test_pools_extended(dolos_session, blockfrost_session, api_comparator):
    """Test /pools/extended endpoint."""
    endpoint = "/pools/extended"

    dolos_response = dolos_session.get(f"{DOLOS_BASE_URL}{endpoint}")
    blockfrost_response = blockfrost_session.get(
        f"{BLOCKFROST_BASE_URL}{endpoint}"
    )

    assert dolos_response.status_code == 200, (
        f"Dolos API failed: {dolos_response.text}"
    )
    assert blockfrost_response.status_code == 200, (
        f"Blockfrost API failed: {blockfrost_response.text}"
    )

    is_identical, violations = api_comparator.compare_responses(
        dolos_response.json(),
        blockfrost_response.json(),
        endpoint
    )

    if not is_identical:
        pytest.fail("\n".join(violations))


def test_account_rewards(dolos_session, blockfrost_session, api_comparator):
    """Test /accounts/{stake_address}/rewards endpoint."""
    endpoint = (
        "/accounts/stake_test1up8590900edfw9qxjmzfxa4jsd992jgj0tvgv3z"
        "md6cvz8cpkrg6h/rewards"
    )

    dolos_response = dolos_session.get(f"{DOLOS_BASE_URL}{endpoint}")
    blockfrost_response = blockfrost_session.get(
        f"{BLOCKFROST_BASE_URL}{endpoint}"
    )

    assert dolos_response.status_code == 200, (
        f"Dolos API failed: {dolos_response.text}"
    )
    assert blockfrost_response.status_code == 200, (
        f"Blockfrost API failed: {blockfrost_response.text}"
    )

    is_identical, violations = api_comparator.compare_responses(
        dolos_response.json(),
        blockfrost_response.json(),
        endpoint
    )

    if not is_identical:
        pytest.fail("\n".join(violations))


def test_pool_history(dolos_session, blockfrost_session, api_comparator):
    """Test /pools/{pool_id}/history endpoint with query parameters."""
    endpoint = (
        "/pools/pool1elet8uart9cuw3lmntqhfn2f44rf52dg6v5ppzkcysxx2"
        "68s43n/history?order=desc&count=50"
    )

    dolos_response = dolos_session.get(f"{DOLOS_BASE_URL}{endpoint}")
    blockfrost_response = blockfrost_session.get(
        f"{BLOCKFROST_BASE_URL}{endpoint}"
    )

    assert dolos_response.status_code == 200, (
        f"Dolos API failed: {dolos_response.text}"
    )
    assert blockfrost_response.status_code == 200, (
        f"Blockfrost API failed: {blockfrost_response.text}"
    )

    is_identical, violations = api_comparator.compare_responses(
        dolos_response.json(),
        blockfrost_response.json(),
        endpoint
    )

    if not is_identical:
        pytest.fail("\n".join(violations))


def test_script_datum(dolos_session, blockfrost_session, api_comparator):
    """Test /scripts/datum/{datum_hash} endpoint."""
    endpoint = (
        "/scripts/datum/0041bf96b13f74bcf6fa9c12aa53a5a4be5ce82d755b578"
        "d8cb8131331f5de9a"
    )

    dolos_response = dolos_session.get(f"{DOLOS_BASE_URL}{endpoint}")
    blockfrost_response = blockfrost_session.get(
        f"{BLOCKFROST_BASE_URL}{endpoint}"
    )

    assert dolos_response.status_code == 200, (
        f"Dolos API failed: {dolos_response.text}"
    )
    assert blockfrost_response.status_code == 200, (
        f"Blockfrost API failed: {blockfrost_response.text}"
    )

    is_identical, violations = api_comparator.compare_responses(
        dolos_response.json(),
        blockfrost_response.json(),
        endpoint
    )

    if not is_identical:
        pytest.fail("\n".join(violations))
