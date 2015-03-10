# -*- coding: utf-8 -*-

import requests

api_key = None
API_BASE_URL = 'https://api.vultr.com/v1'

def yn(flag):
    return 'yes' if flag else 'no'

def server_list():
    json = requests.get(API_BASE_URL + '/server/list', params={'api_key': api_key}).json()
    servers = []

    if not json:
        return servers

    for SUBID, server in json.iteritems():
        servers.append(server)

    return servers

def server_create(label, vpsplanid, osid, dcid, sshkeyid, enable_private_network, enable_backups):
    data = {'label': label, 'VPSPLANID': vpsplanid, 'OSID': osid, 'DCID': dcid,
            'SSHKEYID': sshkeyid, 'enable_private_network': yn(enable_private_network),
            enable_backups: yn(enable_backups)}

    r = requests.post(API_BASE_URL + '/server/create', params={'api_key': api_key}, data=data)
    
    if r.status_code > 200:
        raise Exception('API Error', r.text)

    json = r.json()
    servers = server_list()

    for server in servers:
        if server['SUBID'] == json['SUBID']:
            return server

    return False

def server_destroy(SUBID):
    r = requests.post(API_BASE_URL + '/server/destroy', params={'api_key': api_key}, data={'SUBID': SUBID})
    return True if r.status_code == 200 else False

def server_start(SUBID):
    return requests.post(API_BASE_URL + '/server/start', params={'api_key': api_key})
