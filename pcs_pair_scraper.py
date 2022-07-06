# file gets pairs posted to latest block on pancake swap
from web3 import Web3
from web3.middleware import local_filter_middleware
import json

rpc_url = "https://bsc-dataseed.binance.org/"
wbnb_address = "0xbb4CdB9CBd36B01bD1cBaEBF2De08d9173bc095c"
pcs_factory_address = "0xcA143Ce32Fe78f1f7019d7d551a6402fC5350c73"
pcs_factory_abi = open('evm_factory_abi', 'r').read().replace('\n', '')
web3 = Web3(Web3.HTTPProvider(rpc_url))
web3.middleware_onion.add(local_filter_middleware)
pcs_factory_contract = web3.eth.contract(address=pcs_factory_address, abi=pcs_factory_abi)
new_pair_filter = pcs_factory_contract.events.PairCreated.createFilter(fromBlock='latest')
base_tokens = ['0xbb4C', '0x8AC7', '0xe9e7', '0x0E09', '0x55d3', '0x7130', '0x2170', '0x1AF3']


# gets pairs posted to pcs at latest block
def look_for_new_pairs():
    try:
        global new_pair_filter
        ret = []
        for PairCreated in new_pair_filter.get_new_entries():
            pair = json.loads(Web3.toJSON(PairCreated))
            if Web3.toJSON(PairCreated)[21:27] not in base_tokens:
                print('Token spotted: ' + Web3.toJSON(PairCreated)[21:63] + ' Pair Address: ' + pair['args']['pair'])
                address = pair['args']['token0']
                base_token = pair['args']['token1']
            elif Web3.toJSON(PairCreated)[77:83] in base_tokens:
                continue
            else:
                print('Token spotted: ' + Web3.toJSON(PairCreated)[77:119] + ' Pair Address: ' + pair['args']['pair'])
                address = pair['args']['token1']
                base_token = pair['args']['token0']
            ret.append({'token_address': address, 'pair_address': pair['args']['pair'], 'base_token': base_token})
        return ret
    except Exception as e:
        print(e)
        new_pair_filter = pcs_factory_contract.events.PairCreated.createFilter(fromBlock='latest')


# gets 100 blocks of pairs posted to pcs, starting from start_block
def look_for_historical_pairs(start_block):
    block_event_filter = pcs_factory_contract.events.PairCreated.createFilter(fromBlock=start_block, toBlock=start_block + 50)
    ret = []
    for PairCreated in block_event_filter.get_all_entries():
        pair = json.loads(Web3.toJSON(PairCreated))
        if Web3.toJSON(PairCreated)[21:27] not in base_tokens:
            print('Token spotted: ' + Web3.toJSON(PairCreated)[21:63] + ' Pair Address: ' + pair['args']['pair'])
            address = pair['args']['token0']
            base_token = pair['args']['token1']
        elif Web3.toJSON(PairCreated)[77:83] in base_tokens:
            continue
        else:
            print('Token spotted: ' + Web3.toJSON(PairCreated)[77:119] + ' Pair Address: ' + pair['args']['pair'])
            address = pair['args']['token1']
            base_token = pair['args']['token0']
        ret.append({'token_address': address, 'pair_address': pair['args']['pair'], 'base_token': base_token})
    return ret
