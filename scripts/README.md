# Scripts for SPDD verification

## How to use

1. Build [dolos](https://github.com/txpipe/dolos) release binary from tag or install it via CMD
2. Sync Cardano Preview from scratch to current tip (e.g., via Mythril snapshot) - `./dolos daemon`
3. Stop dolos and generate SPDD for the current epoch: `./dolos data compute-spdd`
4. Copy output of the previous command to spdd.txt file
5. Run `./dolos daemon` again to run dolos locally
6. Set cardano epoch and other configuration variables in the .env file

Run spdd scripts:

```sh
python3 -m venv venv
source venv/bin/activate
python3 pool_stakes_history.py
```

The script will go through pool ids, for each of the id it will call `/pool/history` both from Blockfrost API and Dolos API and check if there is any difference.