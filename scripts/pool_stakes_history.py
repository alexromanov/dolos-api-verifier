import requests
import time
from typing import List, Tuple, Optional
from dotenv import load_dotenv
import os


load_dotenv()

API_KEY = os.getenv("BLOCKFROST_API_KEY")
EPOCH = os.getenv("CARDANO_EPOCH")

TIMEOUT = 5


def parse_pool_delegation_table(content: str) -> List[Tuple[str, int]]:
    results = []
    lines = content.strip().split('\n')

    for line in lines:
        if (line.startswith('+') or line.startswith('|===') or
                'pool' in line.lower()):
            continue
        if line.startswith('|') and line.count('|') >= 3:
            parts = [part.strip() for part in line.split('|')]
            if len(parts) >= 3 and parts[1] and parts[2]:
                pool = parts[1].strip()
                delegation = parts[2].strip()
                if (pool.lower() != 'pool' and
                        delegation.lower() != 'delegation'):
                    results.append((pool, int(delegation)))
    return results


def get_pool_active_stake(pool_id: str, epoch: str,
                          api_key: Optional[str] = None) -> Optional[int]:
    time.sleep(TIMEOUT)
    print(f"Sleep for {TIMEOUT} seconds is over")

    url = (f"https://cardano-preview.blockfrost.io/api/v0/pools/"
           f"{pool_id}/history?order=desc&count=100")

    headers = {}
    if api_key:
        headers['project_id'] = api_key

    try:
        response = requests.get(url, headers=headers, timeout=10)

        if response.status_code == 200:
            data = response.json()
            active_stake = None
            if data and isinstance(data, list):
                for entry in data:
                    if str(entry.get('epoch')) == str(epoch):
                        print(f"Found Blockfrost active stake for pool "
                              f"{pool_id} at epoch {epoch}: "
                              f"{entry.get('active_stake')}")
                        active_stake = int(entry.get('active_stake'))
                        break
            if active_stake is None:
                print(f"No active stake found via Blockfrost API for pool "
                      f"{pool_id} at epoch {epoch}")
            return active_stake

    except requests.exceptions.RequestException as e:
        print(f"Request error for pool {pool_id}: {e}")
        return None


def get_pool_active_stake_from_dolos(pool_id: str,
                                     epoch: str) -> Optional[int]:
    url = (f"http://localhost:3000/pools/{pool_id}/history?"
           f"order=desc&count=100")

    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            active_stake = None
            if data and isinstance(data, list):
                for entry in data:
                    if str(entry.get('epoch')) == str(epoch):
                        print(f"Found Dolos active stake for pool {pool_id} "
                              f"at epoch {epoch}: "
                              f"{entry.get('active_stake')}")
                        active_stake = int(entry.get('active_stake'))
                        break
            if active_stake is None:
                print(f"No active stake found via Dolos API for pool "
                      f"{pool_id} at epoch {epoch}")
            return active_stake
    except requests.exceptions.RequestException as e:
        print(f"Request error for pool {pool_id}: {e}")
        return None


def process_pools_with_active_stake(
        content: str, epoch: str,
        api_key: Optional[str] = None) -> List[dict]:
    parsed_data = parse_pool_delegation_table(content)
    results = []
    for i, (pool_id, delegation) in enumerate(parsed_data):
        print(f"Processing pool {i+1}/{len(parsed_data)}: {pool_id}")
        active_stake = get_pool_active_stake(pool_id, epoch, api_key)

        dolos_active_stake = get_pool_active_stake_from_dolos(pool_id, epoch)

        pool_data = {
            'pool_id': pool_id,
            'delegation': delegation,
            'active_stake': active_stake,
            'dolos_active_stake': dolos_active_stake
        }
        results.append(pool_data)
    return results


if __name__ == "__main__":
    table_content = """
    +------------------------------------------------------+----------------+
    | pool                                                 | delegation     |
    +===================================================================== +
    | 4393ceb8e4838b6103fe41c0947dbfe1ab64d7f6f9d98ec0e8e2a100 | 39498640090  |
    |------------------------------------------------------+----------------|
    | 5107766450180dfea7b74bd56ea8fdaf62032308b13f6e558092227a | 1000049618065|
    """

    api_key = None
    pool_data = process_pools_with_active_stake(table_content, api_key)

    print("\n" + "="*80)
    print("RESULTS")
    print("="*80)

    for data in pool_data:
        if data['active_stake'] != data['delegation']:
            print(f"Discrepancy found for pool {data['pool_id']}:")
            print(f"  Delegation: {data['delegation']:,}")
            active = (data['active_stake'] if data['active_stake']
                      else 'Failed to fetch')
            print(f"  Active Stake: {active}")


def process_pools_from_file(filename: str, epoch: str,
                            api_key: Optional[str] = None) -> List[dict]:
    """
    Read table from file and process pools with active stake.
    """
    with open(filename, 'r') as file:
        content = file.read()

    return process_pools_with_active_stake(content, epoch, api_key)


pool_data = process_pools_from_file('spdd_sample.txt', str(EPOCH), API_KEY)

print("\n" + "="*140)
print("RESULTS TABLE")
print("="*140)
print(f"{'Pool ID':<64} {'Dolos (compute_spdd)':<20} "
      f"{'Blockfrost':<20} {'Dolos API':<20} {'Difference':<15}")
print("-" * 140)

for data in pool_data:
    dolos_value = f"{int(data['delegation']):,}"
    blockfrost_value = (f"{data['active_stake']:,}"
                        if data['active_stake'] is not None
                        else 'Stake not found for epoch 1107')
    dolos_api_value = (f"{data['dolos_active_stake']:,}"
                       if data['dolos_active_stake'] is not None
                       else 'Stake not found for epoch 1107')

    if (data['active_stake'] is not None and
            data['dolos_active_stake'] is not None):
        difference = f"{data['active_stake'] - data['dolos_active_stake']:,}"
    else:
        difference = "N/A"

    print(f"{data['pool_id']:<64} {dolos_value:<20} "
          f"{blockfrost_value:<20} {dolos_api_value:<20} "
          f"{difference:<15}")
