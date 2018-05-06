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
        r = requests.get(self.API_BASE_URL + '/server/list', params={'api_key': self.API_KEY}, timeout=None)

        if r.status_code > 200:
            raise Exception('API Error', r.text)

        servers = []
        json = r.json()

        if not json:
            return servers

        for SUBID, server in json.iteritems():
            servers.append(server)

        return servers

    def server_create(self, label, vpsplanid, osid, dcid, sshkeyid, enable_private_network, enable_backups, isoid=None, snapshotid=None, hostname=None, tag=None, reserved_ip_v4=None, auto_backups=None, ddos_protection=None, notify_activate=None, userdata=None, enable_ipv6=None, scriptid=None):
        # Required or non-null parameters
        data = {'label': label, 'VPSPLANID': vpsplanid, 'OSID': osid, 'DCID': dcid,
                'SSHKEYID': sshkeyid, 'enable_private_network': self.yn(enable_private_network),
                enable_backups: self.yn(enable_backups)}

        # optional parameters
        if isoid:  data['ISOID'] = isoid
        if snapshotid:  data['SNAPSHOTID'] = snapshotid
        if hostname:  data['hostname'] = hostname
        if tag:  data['tag'] = tag
        if reserved_ip_v4:  data['reserved_ip_v4'] = reserved_ip_v4
        data['auto_backups'] = self.yn(auto_backups)
        data['ddos_protection'] = self.yn(ddos_protection)
        data['notify_activate'] = self.yn(notify_activate)
        if enable_ipv6: data['enable_ipv6'] = self.yn(enable_ipv6)
        if scriptid: data['SCRIPTID'] = scriptid
        if userdata: data['userdata'] = userdata

        r = requests.post(self.API_BASE_URL + '/server/create', params={'api_key': self.API_KEY}, data=data, timeout=None)

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
        if r.status_code > 200:
            raise Exception('API Error', r.text)
        return True

    def server_start(self, SUBID):
        r = requests.post(self.API_BASE_URL + '/server/start', params={'api_key': self.API_KEY}, data={'SUBID': SUBID})
        if r.status_code > 200:
            raise Exception('API Error', r.text)
        return True

    def server_stop(self, SUBID):
        r = requests.post(self.API_BASE_URL + '/server/stop', params={'api_key': self.API_KEY}, data={'SUBID': SUBID})
        if r.status_code > 200:
            raise Exception('API Error', r.text)
        return True

    def server_reboot(self, SUBID):
        r = requests.post(self.API_BASE_URL + '/server/reboot', params={'api_key': self.API_KEY}, data={'SUBID': SUBID})
        if r.status_code > 200:
            raise Exception('API Error', r.text)
        return True

    def startupscript_list(self):
        r = requests.get(self.API_BASE_URL + '/startupscript/list', params={'api_key': self.API_KEY})
        if r.status_code > 200:
            raise Exception('API Error', r.text)

        startupscripts = []
        json = r.json()

        if not json:
            return startupscripts

        for SCRIPTID, ss in json.iteritems():
            startupscripts.append(ss)
        
        return startupscripts

    def startupscript_update(self, SCRIPTID, label, script):
        data = {'SCRIPTID':SCRIPTID, 'name':label, 'script':script}
        r = requests.post(self.API_BASE_URL + '/startupscript/update', params={'api_key': self.API_KEY}, data=data, timeout=None)
        if r.status_code > 200:
            raise Exception('API Error', r.text)
        return True

    def startupscript_find_by_id(self, SCRIPTID):
        startupscripts = self.startupscript_list()
        for ss in startupscripts:
            if ss['SCRIPTID'] == SCRIPTID:
                return ss
        return False

    def startupscript_find(self, label, ttype=None):
        if not ttype: ttype = 'boot'
        startupscripts = self.startupscript_list()
        for ss in startupscripts:
            if ss['name'] == label and ss['type'] == ttype:
                return ss
        return False

    def startupscript_ensure(self, label, script, ttype=None):
        if not ttype: ttype = 'boot'
        startupscripts = self.startupscript_list()
        for ss in startupscripts:
            if ss['name'] == label and ss['type'] == ttype:
                ss['updated'] = False
                if ss['script'] != script:
                    self.startupscript_update(ss['SCRIPTID'], label, script)
                    ss['updated'] = True
                return ss
        return False

    def sshkey_list(self):
        r = requests.get(self.API_BASE_URL + '/sshkey/list', params={'api_key': self.API_KEY})
        if r.status_code > 200:
            raise Exception('API Error', r.text)

        sshkeys = []
        json = r.json()

        if not json:
            return sshkeys

        for SSHKEYID, ss in json.iteritems():
            sshkeys.append(ss)
        
        return sshkeys

    def sshkey_update(self, SSHKEYID, label, sshkey):
        data = {'SSHKEYID':SSHKEYID, 'name':label, 'ssh_key':sshkey}
        r = requests.post(self.API_BASE_URL + '/sshkey/update', params={'api_key': self.API_KEY}, data=data, timeout=None)
        if r.status_code > 200:
            raise Exception('API Error', r.text)
        return True

    def sshkey_find_by_id(self, SSHKEYID):
        sshkeys = self.sshkey_list()
        for ss in sshkeys:
            if ss['SSHKEYID'] == SSHKEYID:
                return ss
        return False

    def sshkey_find(self, label, ttype=None):
        if not ttype: ttype = 'boot'
        sshkeys = self.sshkey_list()
        for ss in sshkeys:
            if ss['name'] == label:
                return ss
        return False

    def sshkey_ensure(self, label, sshkey, ttype=None):
        if not ttype: ttype = 'boot'
        sshkeys = self.sshkey_list()
        for ss in sshkeys:
            if ss['name'] == label:
                ss['updated'] = False
                if ss['ssh_key'] != sshkey:
                    self.sshkey_update(ss['SSHKEYID'], label, sshkey)
                    ss['updated'] = True
                return ss
        return False

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

    def stop(self):
        assert self.status == 'active', 'The server is not active.'
        assert self.power_status == 'running', 'Server is not running.'
        driver.server_stop(self.SUBID)

    def reboot(self):
        assert self.status == 'active', 'The server is not active.'
        assert self.power_status != 'running', 'Server already running.'
        driver.server_reboot(self.SUBID)

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
            main_gw=self.gateway_v4,
            main_mask=self.netmask_v4,
            v6_main_ip=self.v6_main_ip,
            v6_network=self.v6_network,
            internal_ip=self.internal_ip,
            status=self.status,
            power_status=self.power_status,
            default_password=self.default_password,
            location=self.location,
            os=self.os
        )

    def ansible_facts(self):
        return dict(
            label=self.label,
            main_ip=self.main_ip,
            internal_ip=self.internal_ip,
            ip_address=self.main_ip,
            private_ip_address=self.internal_ip,
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
    def add(cls, label, VPSPLANID, OSID, DCID, SSHKEYID=None, enable_private_network=False, enable_backups=False, ISOID=None, snapshotid=None, hostname=None, tag=None, reserved_ip_v4=None, auto_backups=None, ddos_protection=None, notify_activate=None, userdata=None, scriptid=None, enable_ipv6=None):
        json = driver.server_create(label, VPSPLANID, OSID, DCID, SSHKEYID, enable_private_network, enable_backups,ISOID,snapshotid,hostname,tag,reserved_ip_v4,auto_backups,ddos_protection,notify_activate, userdata, scriptid, enable_ipv6)
        return cls(json)

class Startupscript:
    def __init__(self, startupscript_json):
        self.date_created = None
        self.__dict__.update(startupscript_json)

    def update_attrs(self, attrs=None):
        if attrs:
            for k, v in attrs.iteritems():
                setattr(self, k, v)
        else:
            json = Startupscript.find(self.SCRIPTID).to_json()
            if json:
                self.update_attrs(json)
    
    @classmethod
    def findByID(cls, SCRIPTID):
        json = driver.startupscript_find_by_id(SCRIPTID)
        return cls(json)
    
    @classmethod
    def find(cls, label, ttype=None):
        json = driver.startupscript_find(label, ttype)
        return cls(json)

    @classmethod
    def ensure(cls, label, script, ttype=None):
        json = driver.startupscript_ensure(label, script, ttype)
        return cls(json)

class Sshkey:
    def __init__(self, sshkey_json):
        self.date_created = None
        self.__dict__.update(sshkey_json)

    def update_attrs(self, attrs=None):
        if attrs:
            for k, v in attrs.iteritems():
                setattr(self, k, v)
        else:
            json = Sshkey.find(self.SSHKEYID).to_json()
            if json:
                self.update_attrs(json)
    
    @classmethod
    def findByID(cls, SSHKEYID):
        json = driver.sshkey_find_by_id(SSHKEYID)
        return cls(json)
    
    @classmethod
    def find(cls, label, ttype=None):
        json = driver.sshkey_find(label, ttype)
        return cls(json)

    @classmethod
    def ensure(cls, label, sshkey, ttype=None):
        json = driver.sshkey_ensure(label, sshkey, ttype)
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

    if command == 'sshkey':
        global driver
        driver = Driver(api_key)
        action = module.params['action']
        changed = False
        if action == 'getid':
            ss = Sshkey.find(label=getkeyordie('label'))
            if ss.SSHKEYID: changed=True
            module.exit_json(changed=changed, sshkeyid=ss.SSHKEYID)
        if action == 'ensure':
            ss = Sshkey.ensure(
                label=getkeyordie('label'),
                sshkey=getkeyordie('sshkey'))
            if ss.updated: changed=True
            module.exit_json(changed=changed, sshkeyid=ss.SSHKEYID)

    if command == 'startupscript':
        global driver
        driver = Driver(api_key)
        action = module.params['action']
        changed = False
        if action == 'getid':
            ss = Startupscript.find(label=getkeyordie('label'))
            if ss.SCRIPTID: changed=True
            module.exit_json(changed=changed, scriptid=ss.SCRIPTID)
        if action == 'ensure':
            ss = Startupscript.ensure(
                label=getkeyordie('label'),
                script=getkeyordie('script'))
            if ss.updated: changed=True
            module.exit_json(changed=changed, scriptid=ss.SCRIPTID)

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
                    ISOID=module.params['ISOID'],
                    DCID=getkeyordie('DCID'),
                    SSHKEYID=module.params['SSHKEYID'],
                    enable_private_network=module.params['enable_private_network'],
                    enable_backups=module.params['enable_backups'],
                    enable_ipv6=module.params['enable_ipv6'],
                    snapshotid=module.params['snapshotid'],
                    hostname=module.params['hostname'],
                    tag=module.params['tag'],
                    reserved_ip_v4=module.params['reserved_ip_v4'],
                    auto_backups=module.params['auto_backups'],
                    ddos_protection=module.params['ddos_protection'],
                    notify_activate=module.params['notify_activate'],
                    userdata=module.params['userdata'],
                    SCRIPTID=module.params['SCRIPTID'],
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
            command = dict(choices=['server', 'ssh', 'dns', 'startupscript', 'sshkey'], default='server'),
            action = dict(type='str', default=''),
            state = dict(choices=['active', 'present', 'pending', 'absent'], default='present'),
            api_key = dict(no_log=True),
            label = dict(aliases=['name'], type='str'),
            hostname = dict(type='str', default=''),
            SUBID = dict(aliases=['id'], type='int'),
            VPSPLANID = dict(type='int'),
            OSID = dict(type='int'),
            ISOID = dict(type='int', default=0),
            DCID = dict(type='int'),
            SSHKEYID = dict(default=''),
            SCRIPTID = dict(type='str', default=''),
            userdata = dict(type='str', default=''),
            enable_private_network = dict(type='bool', default='no'),
            enable_backups = dict(type='bool', default='no'),
            enable_ipv6 = dict(type='bool', default='yes'),
            unique_label = dict(aliases=['unique_name'], type='bool', default='yes'),
            wait = dict(type='bool', default=True),
            wait_timeout = dict(default=30000, type='int'),
            notify_activate = dict(type='bool', default='no'),
            ddos_protection = dict(type='bool', default='no'),
            auto_backups = dict(type='bool', default='no'),
            reserved_ip_v4 = dict(type='str', default=''),
            tag = dict(type='str', default=''),
            script = dict(type='str', default=''),
            sshkey = dict(type='str', default=''),
            snapshotid = dict(type='str', default='')
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
