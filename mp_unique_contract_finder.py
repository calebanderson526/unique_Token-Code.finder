import json
from web3 import Web3
from web3.middleware import local_filter_middleware
import pcs_pair_scraper
import fork_detector
import time
import asyncio
import multiprocessing


load_data = True
starting_block = 18236906
token_count = 0
tested_addresses = []


def test_tokens(token_dict, token_queue, lock, is_finished):
    while is_finished.get() == 0:
        time.sleep(1)
        if not token_queue.empty():
            lock.acquire()
            token = token_queue.get()
            lock.release()
        else:
            continue
        cur_dict = token_dict
        test_result = fork_detector.detect_fork_with_mp_dict_and_code(token, cur_dict)
        if not test_result['verified']:
            continue
        if test_result['result']:
            d = token_dict[test_result['original']['token_address']]
            d['forks'].append({'token_address': token['token_address'],
                               'name': token['name'],
                               'pair_address': token['pair_address']})
            token_dict[test_result['original']['token_address']] = d
            continue
        token_dict[token['token_address']] = {
            'code': token['code'],
            'name': token['name'],
            'pair_address': token['pair_address'],
            'base_token': token['base_token'],
            'forks': []
                                              }


def update_storage(token_dict):
    print('updating storage')
    token_json = json.dumps(token_dict.copy(), indent=4)
    with open('token_data.json', 'w') as file:
        file.write(token_json)
    with open('all_pcs_tokens.json', 'w') as file2:
        file2.write(json.dumps(tested_addresses, indent=4))


async def main():
    global token_count
    global tested_addresses
    processes = []
    manager = multiprocessing.Manager()
    token_dict = manager.dict()
    token_queue = manager.Queue()
    lock = multiprocessing.Lock()
    is_finished = manager.Value('i', 0)
    if load_data:
        print('loading data')
        with open('token_data.json', 'r') as token_data_json:
            data_from_file = json.load(token_data_json)
            token_dict = manager.dict(data_from_file)
            for k in data_from_file:
                tested_addresses.append(k)
                for f in data_from_file[k]['forks']:
                    tested_addresses.append(f['token_address'])

    avail_cpus = multiprocessing.cpu_count()
    for i in range(0, avail_cpus - 1):
        processes.append(multiprocessing.Process(target=test_tokens, args=(token_dict, token_queue, lock, is_finished)))
        processes[i].start()
    rpc_url = 'https://bsc-dataseed.binance.org/'
    web3 = Web3(Web3.HTTPProvider(rpc_url))
    web3.middleware_onion.add(local_filter_middleware)
    print('Data Collection Starting')
    i = starting_block
    end_block = web3.eth.get_block_number()
    start_time = time.perf_counter()

    async def get_code(pair):
        token_shortened_code = fork_detector.get_shortened_token_code(pair['token_address'])
        if not token_shortened_code['verified']:
            print(token_shortened_code['token_address'] + ' is not verified')
        else:
            token_shortened_code['pair_address'] = pair['pair_address']
            token_shortened_code['base_token'] = pair['base_token']
            if token_shortened_code['token_address'] not in tested_addresses:
                token_queue.put(manager.dict(token_shortened_code))
                tested_addresses.append(token_shortened_code['token_address'])
            else:
                print('duplicate')

    async def scrape_pairs():
        global token_count
        global tested_addresses
        try:
            get_code_time = time.perf_counter()
            for pair in pcs_pair_scraper.look_for_historical_pairs(i):
                asyncio.create_task(get_code(pair))
                await asyncio.sleep(.201 - abs(time.perf_counter() - get_code_time))
                token_count += 1
        except ValueError as ve:
            await asyncio.sleep(5)
            print(str(ve))
        except Exception as er:
            print('UNCAUGHT EXCEPTION SLEEPING 60s')
            print(str(er))
            await asyncio.sleep(60)

    while i < end_block:
        try:
            iter_time = time.perf_counter()
            asyncio.create_task(scrape_pairs())
            i += 50
            if i % 2000 == 0:
                print('Test has reached block: ' + str(i))
            if token_count % 50 == 0 and not token_count == 0:
                update_storage(token_dict)
                print(str(token_count) + ' tokens, ' + str(i - starting_block) + ' blocks tested in ' +
                      str(time.perf_counter() - start_time))
            await asyncio.sleep(1.501 - abs(time.perf_counter() - iter_time))
        except Exception as e:
            print(e)
            print('CRITICALEXCEPTIONCRITICALEXCEPTIONCRITICALEXCEPTION')
            time.sleep(15)
    while not token_queue.empty():
        pass
    is_finished.set(1)
    for p in processes:
        p.join()
    print('Time to complete Backtest: ' + str(time.perf_counter() - start_time) + ' seconds')
    print('Tokens Tested: ' + str(token_count))
    print('Blocks Tested: ' + str(end_block - starting_block))
    update_storage(token_dict)


if __name__ == '__main__':
    asyncio.run(main())
else:
    pass
