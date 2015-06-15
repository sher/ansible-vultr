#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import os
import time
import requests

driver = None

class Singleton(type):
    def __call__(cls, *args, **kwargs):
        try:
            return cls.__instance
        except AttributeError:
            cls.__instance = super(Singleton, cls).__call__(*args, **kwargs)
            return cls.__instance

class Driver(object):
    __metaclass__ = Singleton

    API_KEY = None
    API_BASE_URL = 'https://api.vultr.com/v1'

    def __init__(self, API_KEY):
        self.API_KEY = API_KEY

    def yn(self, flag):
        return 'yes' if flag else 'no'

    def server_list(self):
        json = requests.get(self.API_BASE_URL + '/server/list', params={'api_key': self.API_KEY}).json()
        servers = []

        if not json:
            return servers

        for SUBID, server in json.iteritems():
            servers.append(server)

        return servers

    def server_create(self, label, vpsplanid, osid, dcid, sshkeyid, enable_private_network, enable_backups):
        data = {'label': label, 'VPSPLANID': vpsplanid, 'OSID': osid, 'DCID': dcid,
                'SSHKEYID': sshkeyid, 'enable_private_network': self.yn(enable_private_network),
                enable_backups: self.yn(enable_backups)}

        r = requests.post(self.API_BASE_URL + '/server/create', params={'api_key': self.API_KEY}, data=data)

        if r.status_code > 200:
            raise Exception('API Error', r.text)

        json = r.json()
        servers = self.server_list()

        for server in servers:
            if server['SUBID'] == json['SUBID']:
                return server

        return False

    def server_destroy(self, SUBID):
        r = requests.post(self.API_BASE_URL + '/server/destroy', params={'api_key': self.API_KEY}, data={'SUBID': SUBID})
        return True if r.status_code == 200 else False

    def server_start(self, SUBID):
        return requests.post(self.API_BASE_URL + '/server/start', params={'api_key': self.API_KEY})

class TimeoutError(Exception):
    def __init__(self, msg, id):
        super(TimeoutError, self).__init__(msg)
        self.id = id

class Server:
    def __init__(self, server_json):
        self.status = 'new'
        self.__dict__.update(server_json)

    def update_attrs(self, attrs=None):
        if attrs:
            for k, v in attrs.iteritems():
                setattr(self, k, v)
        else:
            json = Server.find(self.SUBID).to_json()
            if json:
                self.update_attrs(json)

    def is_running(self):
        return self.status == 'active' and self.power_status == 'running'

    def start(self):
        assert self.status == 'active', 'The server is not active.'
        assert self.power_status != 'running', 'Server already running.'
        driver.server_start(self.SUBID)

    def ensure_running(self, wait=True, wait_timeout=300):
        if self.is_running():
            return

        if self.status == 'active' and self.power_status == 'stopped':
            self.start()

        if wait:
            end_time = time.time() + wait_timeout
            while time.time() < end_time:
                time.sleep(min(20, end_time - time.time()))
                self.update_attrs()

                if self.is_running():
                    if not self.main_ip:
                        raise TimeoutError('No ip is found.', self.SUBID)
                    return
            raise TimeoutError('Wait for server running timeout', self.SUBID)

    def destroy(self):
        return driver.server_destroy(self.SUBID)

    def to_json(self):
        return dict(
            label=self.label,
            SUBID=self.SUBID,
            DCID=self.DCID,
            VPSPLANID=self.VPSPLANID,
            main_ip=self.main_ip,
            internal_ip=self.internal_ip,
            status=self.status,
            power_status=self.power_status,
            location=self.location,
            os=self.os
        )

    def ansible_facts(self):
        return dict(
            label=self.label,
            main_ip=self.main_ip,
            internal_ip=self.internal_ip,
        )

    @classmethod
    def find(cls, SUBID=None, label=None):
        if not SUBID and not label:
            return False

        servers = driver.server_list()

        if not servers:
            return False

        if SUBID:
            for server in servers:
                if server['SUBID'] == SUBID:
                    return cls(server)

        if label:
            for server in servers:
                if server['label'] == label:
                    return cls(server)

        return False

    @classmethod
    def add(cls, label, VPSPLANID, OSID, DCID, SSHKEYID=None, enable_private_network=False, enable_backups=False):
        json = driver.server_create(label, VPSPLANID, OSID, DCID, SSHKEYID, enable_private_network, enable_backups)
        return cls(json)

def core(module):
    def getkeyordie(k):
        v = module.params[k]
        if v is None:
            module.fail_json(msg='Unable to load %s' % k)
        return v

    try:
        api_key = module.params['api_key'] or os.environ['VULTR_API_KEY']
    except KeyError, e:
        module.fail_json(msg='Unable to load %s' % e.message)

    changed = True
    command = module.params['command']
    state = module.params['state']

    if command == 'server':
        global driver
        driver = Driver(api_key)

        if state in ('active', 'present'):
            server = Server.find(SUBID=module.params['SUBID'])

            if not server and module.params['unique_label']:
                server = Server.find(label=getkeyordie('label'))

            if not server:
                server = Server.add(
                    label=getkeyordie('label'),
                    VPSPLANID=getkeyordie('VPSPLANID'),
                    OSID=getkeyordie('OSID'),
                    DCID=getkeyordie('DCID'),
                    SSHKEYID=module.params['SSHKEYID'],
                    enable_private_network=module.params['enable_private_network'],
                    enable_backups=module.params['enable_backups'],
                )

            if server.is_running():
                changed = False

            server.ensure_running(
                wait=getkeyordie('wait'),
                wait_timeout=getkeyordie('wait_timeout')
            )

            module.exit_json(changed=changed, ansible_facts=server.ansible_facts(), server=server.to_json())

        elif state in ('absent', 'deleted'):
            server = Server.find(module.params['SUBID'])
            if not server and module.params['unique_label']:
                server = Server.find(label=getkeyordie('label'))

            if not server:
                module.exit_json(changed=False, msg='The server is not found.')

            ret = server.destroy()

            if not ret:
                module.fail_json(changed=False, msg="Can't destroy server.")

            module.exit_json(changed=True, event={"destroy": True})

def main():
    module = AnsibleModule(
        argument_spec = dict(
            command = dict(choices=['server', 'ssh'], default='server'),
            state = dict(choices=['active', 'present', 'pending', 'absent'], default='present'),
            api_key = dict(no_log=True),
            label = dict(aliases=['name'], type='str'),
            SUBID = dict(aliases=['id'], type='int'),
            VPSPLANID = dict(type='int'),
            OSID = dict(type='int'),
            DCID = dict(type='int'),
            SSHKEYID = dict(default=''),
            enable_private_network = dict(type='bool', default='no'),
            enable_backups = dict(type='bool', default='no'),
            unique_label = dict(aliases=['unique_name'], type='bool', default='yes'),
            wait = dict(type='bool', default=True),
            wait_timeout = dict(default=300, type='int')
        ),
        required_together = (
            ['VPSPLANID', 'DCID', 'OSID'],
        ),
        required_one_of = (
            ['SUBID', 'label'],
        ),
    )

    try:
        core(module)
    except (Exception), e:
        module.fail_json(msg=str(e))

# import module snippets
from ansible.module_utils.basic import *

main()
