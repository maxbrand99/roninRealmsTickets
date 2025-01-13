import json
import time
from web3 import Web3
import concurrent.futures

myKey = "YOUR_PRIVATE_KEY_HERE"
myAddress = Web3.to_checksum_address("YOUR_ADDRESS_HERE")
totalNum = 0

# PLEASE DO NOT MAKE THIS HIGHER THAN 50 OR IT WILL CAUSE ISSUES
gasPrice = 25

contractAddress = Web3.to_checksum_address("0x451932bffd336406585479b87ce0fac96330f5f0")
w3 = Web3(Web3.HTTPProvider('https://api.roninchain.com/rpc'))
launchpadContract = w3.eth.contract(address=Web3.to_checksum_address("0xa8e9fdf57bbd991c3f494273198606632769db99"), abi=json.loads('[{"inputs":[{"internalType":"enum ILaunchpadStructs.StageType","name":"stageType","type":"uint8"},{"internalType":"bytes","name":"data","type":"bytes"}],"name":"execute","outputs":[{"internalType":"bytes","name":"","type":"bytes"}],"stateMutability":"payable","type":"function"}]'))
txs = []
totalMinted = 0

def mintTx(abiData, nonce, amount):
    mint_txn = launchpadContract.functions.execute(
        1,
        abiData
    ).build_transaction({
        'chainId': 2020,
        'gas': int(200000 * amount),
        'gasPrice': Web3.to_wei(gasPrice, 'gwei'),
        'nonce': nonce
    })
    signed_txn = w3.eth.account.sign_transaction(mint_txn, private_key=myKey)
    return signed_txn


def sendTxSingle(signed_txn):
    try:
        w3.eth.send_raw_transaction(signed_txn.rawTransaction)
    except Exception as e:
        print(e)
    tx = signed_txn.hash
    attempts = 0
    while attempts < 10:
        try:
            receipt = w3.eth.wait_for_transaction_receipt(tx, 10, 1)
            if receipt["status"] == 1:
                print(f"success\t" + w3.to_hex(w3.keccak(signed_txn.rawTransaction)))
            else:
                print(f"fail\t" + w3.to_hex(w3.keccak(signed_txn.rawTransaction)))
        except Exception as e:
            print(e)
            time.sleep(5)
        attempts += 1
    print(f"Failed after 10 attempts: {signed_txn}")


print(f"Building txs")
nonce = w3.eth.get_transaction_count(myAddress)
while True:
    amount = min(150, totalNum - totalMinted)
    if amount == 0:
        break
    totalMinted += amount
    abiData = '0x55110a0c0000000000000000000000000000000000000000000000000000000000000020000000000000000000000000' + str(contractAddress[2:]) + '000000000000000000000000'
    abiData += myAddress[2:]
    abiData += '0' * (64 - len(Web3.to_hex(amount)[2:])) + Web3.to_hex(amount)[2:]
    abiData += '000000000000000000000000000000000000000000000000000000000000000100000000000000000000000000000000000000000000000000000000000000ff00000000000000000000000000000000000000000000000000000000000000c000000000000000000000000000000000000000000000000000000000000000010000000000000000000000000000000000000000000000000000000000000000'
    tx = mintTx(abiData, nonce, amount)
    nonce += 1
    txs.append(tx)

with concurrent.futures.ThreadPoolExecutor(max_workers=25) as executor:
    future_to_url = (executor.submit(sendTxSingle, tx) for tx in txs)
    for future in concurrent.futures.as_completed(future_to_url):
        future.result()