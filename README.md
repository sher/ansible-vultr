# vupy
Create/delete servers in Vultr.

## Usage
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

    - name: Add Vultr hosts to inventory groups
      add_host:
        name: "{{ item.1.server.main_ip }}"
        groups: "cloud,{{ servers[item.0].group }},{{ item.1.server.label }}"
        label: "{{ item.1.server.label }}"
        internal_ip: "{{ item.1.server.internal_ip }}"
      when: item.1.server is defined
      with_indexed_items: created_servers.results
```
