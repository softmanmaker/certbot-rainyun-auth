import os
import time
import requests
import argparse
import tldextract
import json

class Domain:
    def __init__(self, id: int, apikey: str):
        self.url = f'https://api.v2.rainyun.com/product/domain/{id}/dns/'
        self.header = {
            'x-api-key': apikey
        }
        self.records = dict()
    def refresh_dns(self):
        self.records = dict()
        level = dict()
        page_no = 1
        while True:
            response = requests.request('GET', f'{self.url}?limit=500&page_no={page_no}', headers=self.header)
            resp = response.json()
            assert resp['code'] == 200, f'HTTP error {resp['code']}'
            if not resp['data']['Records'] or resp['data']['Records'][0]['record_id'] in self.records.values():
                break
            for record in resp['data']['Records']:
                if not (record['host'] in self.records.keys()):
                    self.records[record['host']] = record['record_id']
                    level[record['host']] = record['level']
                elif record['level'] > level[record['host']]:
                    self.records[record['host']] = record['record_id']
                    level[record['host']] = record['level']
            if resp['data']['TotalRecords'] < 500:
                break
            page_no = page_no + 1
    def get_dns(self):
        if not self.records:
            self.refresh_dns()
    def exist_auth_dns(self):
        self.get_dns()
        return '_acme-challenge' in self.records.keys()
    def add_auth_dns(self, text: str):
        assert not self.exist_auth_dns(), 'DNS already exists.'
        payload = json.dumps({
            "host": "_acme-challenge",
            "level": 10,
            "line": "DEFAULT",
            "ttl": 300,
            "type": "TXT",
            "value": text
        })
        response = requests.request('POST', self.url, headers=self.header, data=payload)
        resp = response.json()
        assert resp['code'] == 200, f'HTTP error {resp['code']}'
    def modify_auth_dns(self, text: str):
        assert self.exist_auth_dns(), "DNS doesn't exist."
        payload = json.dumps({
            "host": "_acme-challenge",
            "level": 10,
            "line": "DEFAULT",
            'record_id': self.records['_acme-challenge'],
            "ttl": 300,
            "type": "TXT",
            "value": text
        })
        response = requests.request('PATCH', self.url, headers=self.header, data=payload)
        resp = response.json()
        assert resp['code'] == 200, f'HTTP error {resp['code']}'
    def clear_auth_dns(self):
        assert self.exist_auth_dns(), "DNS doesn't exist."
        response = requests.request('DELETE', f'{self.url}?record_id={self.records['_acme-challenge']}', headers=self.header)
        resp = response.json()
        assert resp['code'] == 200, f'HTTP error {resp['code']}'

def create_parser():
    parser = argparse.ArgumentParser(description = 'A tool that automates Cerabot DNS challenge process.')
    parser.add_argument('action', help = 'Action to be done. Can be "auth" or "clear".', choices = ['auth', 'clear'])
    parser.add_argument('-k', '--key', help = 'API key of your rainyun account.', type = str)
    parser.add_argument('-i', '--id', help = 'The ID(s) of your domain(s) being authenticated.', nargs = 2, action = 'append', required = True, metavar = ('domain', 'id'))
    return parser

if __name__ == '__main__':
    parser = create_parser()
    args = parser.parse_args()
    if not args.key:
        apikey = os.environ.get('RAINYUN_APIKEY')
    else:
        apikey = args.key
    assert apikey, 'Rainyun API key missing. Abort.'
    ids = dict(args.id)
    authDomain = tldextract.extract(os.environ.get('CERTBOT_DOMAIN')).top_domain_under_public_suffix
    assert authDomain in ids.keys(), f'Please provide the id for {authDomain}.'
    domain = Domain(ids[authDomain], apikey)
    if args.action == 'auth':
        authText = os.environ.get('CERTBOT_VALIDATION')
        if domain.exist_auth_dns():
            domain.modify_auth_dns(authText)
        else:
            domain.add_auth_dns(authText)
        time.sleep(20)
    elif args.action == 'clear':
        if domain.exist_auth_dns():
            domain.clear_auth_dns()