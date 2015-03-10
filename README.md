# vupy
Ansible module for creating / deleting servers in Vultr.
__At the moment the module supports only server creation and destruction.__

## Usage example

This is the main playbook for dynamic inventory provisioning using Vultr.
```yaml
---
- hosts: localhost
  connection: local
  gather_facts: false

  vars:
    api_key: YOUR_API_KEY
    servers:
      # ------------------------------------------------
      # - backend
      # ------------------------------------------------
      - { label: "api.example.com",  group: "lb" }
      - { label: "app1.example.com", group: "app" }
      - { label: "app2.example.com", group: "app" }
      - { label: "mdb1.example.com", group: "db" }
      # ------------------------------------------------
      # - frotnend
      # ------------------------------------------------
      - { label: "example.com", group: "web" }
  tasks:
    - name: Provision Vultr servers
      vultr:
        command: server
        api_key: "{{ api_key }}"
        state: "{{ item.state | default('present') }}"
        label: "{{ item.label }}"
        DCID: "{{ item.DCID | default(25) }}" # Tokyo
        VPSPLANID: "{{ item.VPSPLANID | default(32) }}" # 1024MB / 20GB SSD
        OSID: "{{ item.OSID | default(167) }}" # CentOS 7x64
        SSHKEYID: "{{ item.SSHKEYID | default(YOUR_SSH_KEY_ID) }}"
        enable_private_network: yes
        unique_label: yes
      register: created_servers
      with_items: servers
    # ------------------------------------------------
    # - Append servers to corresponding groups
    # ------------------------------------------------
    - name: Add Vultr hosts to inventory groups
      add_host:
        name: "{{ item.1.server.main_ip }}"
        groups: "cloud,{{ servers[item.0].group }},{{ item.1.server.label }}"
        label: "{{ item.1.server.label }}"
        internal_ip: "{{ item.1.server.internal_ip }}"
      when: item.1.server is defined
      with_indexed_items: created_servers.results

# ------------------------------------------------
# - Run below tasks on group 'cloud', which contains
# - all servers being provisioned
# ------------------------------------------------
- hosts: cloud
  remote_user: root

  tasks:
    - name: Wait for port 22 to become available
      local_action: "wait_for port=22 host={{ inventory_hostname }}"

    - name: Ping pong all hosts
      ping:

    - name: Ensure hostname is preserved in cloud-init
      lineinfile: "dest=/etc/cloud/cloud.cfg regexp='^preserve_hostname' line='preserve_hostname: true' state=present"

    - name: Set hostname in sysconfigs
      lineinfile: dest=/etc/sysconfig/network regexp="^HOSTNAME" line='HOSTNAME="{{ hostvars[inventory_hostname].label }}"' state=present
      register: hostname

    - name: Set hosts FQDN
      lineinfile: dest=/etc/hosts regexp=".*{{ hostvars[inventory_hostname].label }}$" line="{{ inventory_hostname }} {{ hostvars[inventory_hostname].label }}" state=present
      register: fqdn

    - name: Set hostname
      hostname: name={{ hostvars[inventory_hostname].label }}
      when: hostname.changed or fqdn.changed

    - name: Configure eth1 (private network)
      template: src=ifcfg-eth1.j2 dest=/etc/sysconfig/network-scripts/ifcfg-eth1
      register: ifcfg_eth1

    - name: Enable eth1 (private network)
      service: name=network state=restarted
      when: hostname.changed or fqdn.changed or ifcfg_eth1.changed
```
As stated in "Enable eth1 (private network)" task, below is the interface config file.
this file should be localed in the same folder as the playbook.
```ini
# ifcgf-eth1.j2
DEVICE="eth1"
ONBOOT="yes"
NM_CONTROLLED="no"
BOOTPROTO="static"
IPADDR="{{ hostvars[inventory_hostname].internal_ip }}"
NETMASK="255.255.0.0"
IPV6INIT="no"
```
