import random
import re
import threading
from difflib import SequenceMatcher
import requests

bsc_url = 'https://api.bscscan.com/api?module=contract&action=getsourcecode&address='
api_keys = ['&apikey=4NV73QWVWDSUP4UKQSH4IYT4S31PQ2S5RP', '&apikey=QDBFS6AA8DUBREDBD1P6TVK1Z5G4YUF4PF']
original_fork_addresses = ['0xe5ba47fd94cb645ba4119222e34fb33f59c7cd90',
                           '0x8AC76a51cc950d9822D68b83fE1Ad97B32Cd580d',
                           '0xbb4CdB9CBd36B01bD1cBaEBF2De08d9173bc095c',
                           '0x4e3cabd3ad77420ff9031d19899594041c420aee',
                           '0x4a2c860cEC6471b9F5F5a336eB4F38bb21683c98']  # put addresses of token(s) to watch for forks here
fork_code = {}


def get_shortened_token_code(token):
    r = requests.get(bsc_url + token + api_keys[random.choice([0, 1])]).json()
    if r['result'][0]['SourceCode'] == '':
        return {'verified': False, 'token_address': token}
    else:
        return {
                'verified': True,
                'token_address': token,
                'code': code_shortener(r['result'][0]['SourceCode']),
                'name': r['result'][0]['ContractName']
                }


def get_token_code(token):
    r = requests.get(bsc_url + token + api_keys[random.choice([0, 1])]).json()
    if r['result'][0]['SourceCode'] == '':
        return {'verified': False, 'token_address': token}
    else:
        return {
            'verified': True,
            'code': r['result'][0]['SourceCode'],
            'token_address': token,
            'name': r['result'][0]['ContractName']
        }


# Trim comments from code, returning first letter of each word
def code_shortener(text):  # mostly courtesy of stack overflow
    def replacer(match):
        s = match.group(0)
        if s.startswith('/'):
            return " "  # note: a space and not an empty string
        else:
            return s

    pattern = re.compile(
        r'//.*?$|/\*.*?\*/|\'(?:\\.|[^\\\'])*\'|"(?:\\.|[^\\"])*"',
        re.DOTALL | re.MULTILINE
    )
    ret = ''
    trimmed_code = re.sub(pattern, replacer, text)
    split_code = trimmed_code.split()
    for word in split_code:
        ret += word[0]
    return ret


# call this method to detect forks with preloaded contracts that are in this file
def detect_fork(token):
    return detect_fork_with_dict(token, fork_code)


# call this method to detect forks while passing a dict of contracts
def detect_fork_with_dict(token, dict_of_contracts):
    try:
        new_token_code_json = requests.get(bsc_url + token + api_keys[0]).json()
        new_token_code = new_token_code_json['result'][0]['SourceCode']
        if new_token_code == '':
            print('New Token is not verified, passing: ' + token)
            return {'result': False, 'verified': False}
        else:
            shortened_new_token_code = code_shortener(new_token_code)
            return detect_fork_with_dict_and_code({'address': token, 'code': shortened_new_token_code},
                                                  dict_of_contracts)
    except Exception as e:
        print(str(e))
        return {'result': False}


def detect_fork_with_dict_and_code(token_with_code, dict_of_contracts):
    try:
        max_match = {
            'address': '',
            'max_num': 0
        }
        recent_dict = dict_of_contracts.copy()
        for key in recent_dict:
            code_match_num = SequenceMatcher(None, token_with_code['code'], dict_of_contracts[key]).ratio()
            if code_match_num > 0.96:
                print('Fork Detected!!!: ' + token_with_code['token_address'])
                result_file = open('forked_tokens.txt', 'a')
                result_file.write('Original: ' + key + ' New Fork: ' + token_with_code['token_address'] + '\n')
                return {'result': True, 'verified': True, 'original': key, 'code': dict_of_contracts[key]}
        print('Token is not a fork: ' + token_with_code['token_address'])
        print('Closest matching token and ratio: ' + str(max_match))
        return {'result': False, 'verified': True, 'code': token_with_code['code']}

    except Exception as e:
        print(str(e))
        return {'result': False}


def detect_fork_with_mp_dict_and_code(token_with_code, mp_dict_of_tokens):
    max_match = {
        'address': '',
        'max_num': 0
    }
    for key in mp_dict_of_tokens.keys():
        code_match_num = SequenceMatcher(None, token_with_code['code'], mp_dict_of_tokens[key]['code']).ratio()
        if code_match_num > max_match['max_num'] and key != token_with_code['token_address']:
            max_match = {
                'address': key,
                'max_num': code_match_num
            }
        if code_match_num > 0.96 and key != token_with_code['token_address']:
            print('Fork Spotted: ' + token_with_code['token_address'])
            print(max_match)
            return {'result': True,
                    'verified': True,
                    'original': {
                        'token_address': key,
                        'name': mp_dict_of_tokens[key]['name'],
                        'pair_address': mp_dict_of_tokens[key]['pair_address'],
                        'max_match': max_match
                    }
                    }
    print('Unique Token Spotted: ' + token_with_code['token_address'])
    print('Closest matching token and ratio: ' + str(max_match))
    return {'result': False, 'verified': True, 'code': token_with_code['code'], 'max_match': max_match}


def initialize():
    try:
        for address in original_fork_addresses:
            code_json = requests.get(bsc_url + address + api_key[0]).json()
            code = code_json['result'][0]['SourceCode']
            if code == '':
                print('A token in original fork addresses is not verified')
            else:
                shortened_code = code_shortener(code)
                fork_code[address] = shortened_code
    except Exception as e:
        print(e)
