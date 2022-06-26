#!/usr/bin/env python3

import json
import re
import subprocess

from pprint import pprint

# Example announce dict
announce = {
   "exabgp":"4.0.1",
   "time":1655825609.2727358,
   "host":"8e9e652ed857",
   "pid":883761,
   "ppid":1931,
   "counter":3,
   "type":"update",
   "neighbor":{
      "address":{
         "local":"192.168.29.11",
         "peer":"192.168.29.1"
      },
      "asn":{
         "local":65002,
         "peer":65001
      },
      "direction":"in",
      "message":{
         "update":{
            "attribute":{
               "origin":"igp",
               "as-path":[
                  65001
               ],
               "confederation-path":[

               ],
               "extended-community":[
                  {
                     "value":9225060886715039744,
                     "string":"rate-limit:0"
                  }
               ]
            },
            "announce":{
               "ipv4 flow":{
                  "no-nexthop":[
                     {
                        "source-ipv4":[
                           "192.0.2.33/32"
                        ],
                        "string":"flow source-ipv4 192.0.2.33/32"
                     },
                     {
                        "destination-ipv4":[
                           "192.0.2.5/32"
                        ],
                        "protocol":[
                           "=tcp"
                        ],
                        "port":[
                           "=80"
                        ],
                        "destination-port":[
                           "=3128"
                        ],
                        "source-port":[
                           "=8888"
                        ],
                        "string":"flow destination-ipv4 192.0.2.5/32 protocol =tcp port =80 destination-port =3128 source-port =8888"
                     }
                  ]
               }
            }
         }
      }
   }
}

# Example withdraw dict
withdraw = {
   "exabgp":"4.0.1",
   "time":1655820304.7385623,
   "host":"8e9e652ed857",
   "pid":857236,
   "ppid":1931,
   "counter":5,
   "type":"update",
   "neighbor":{
      "address":{
         "local":"192.168.29.11",
         "peer":"192.168.29.1"
      },
      "asn":{
         "local":65002,
         "peer":65001
      },
      "direction":"in",
      "message":{
         "update":{
            "withdraw":{
               "ipv4 flow":[
                  {
                     "source-ipv4":[
                        "192.0.2.33/32"
                     ],
                     "string":"flow source-ipv4 192.0.2.33/32"
                  },
                  {
                     "destination-ipv4":[
                        "192.0.2.5/32"
                     ],
                     "protocol":[
                        "=tcp"
                     ],
                     "string":"flow destination-ipv4 192.0.2.5/32 protocol =tcp"
                  }
               ]
            }
         }
      }
   }
}

data = announce
#data = withdraw

table = 'flowspec'
chain = 'drop_flow_routes'


def run_rc(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE):
    """
    Run command, get return code
    On success:
        * rc + stdout:
    On fail:
        * rc + stderr
    % run_rc('uname')
    (0, 'Linux\n')
    % run_rc('ip link show dev eth99')
    (1, 'Device "eth99" does not exist.\n')
    """
    command = command.split()
    response = subprocess.run(command, stdout=stdout, stderr=stderr, encoding='utf-8')
    rc = response.returncode
    if rc == 0:
        return rc, response.stdout
    return rc, response.stderr


def nft_add_table(name='flowspec'):
    print(f'DEBUG: sudo nft -- add table ip {name}')
    run_rc(f'sudo nft -- add table ip {name}')


def nft_add_chain(chain_name, table_name, hook='prerouting', priority='-300'):
    print(f"DEBUG: sudo nft -- add chain ip {table_name} {chain_name} "
          f"'{{ type filter hook {hook} priority {priority}; policy accept; }}'")
    run_rc(f"sudo nft -- add chain ip {table_name} {chain_name} "
           f"'{{ type filter hook {hook} priority -300; policy accept; }}'")


def nft_add_rule(table_name, chain_name, command=''):
    print(f'DEBUG: sudo nft add rule ip {table_name} {chain_name} {command}')
    run_rc(f'sudo nft add rule ip {table_name} {chain_name} {command}')


def nft_del_rule(table_name, chain_name, command=''):
    print(f'DEBUG: sudo nft delete rule ip {table_name} {chain_name} {command}')
    run_rc(f'sudo nft delete rule ip {table_name} {chain_name} {command}')


if data.get('neighbor', {}).get('message', {}).get('update',{}):
    nft_add_table('flowspec')
    nft_add_chain('drop_flow_routes', 'flowspec')
    for message, config in data['neighbor']['message']['update'].items():
        if message != 'announce' and message != 'withdraw':
            continue
        if 'announce' in message:
            flow_path = config['ipv4 flow']['no-nexthop']
            action_nft = 'add_filter'
        if 'withdraw' in message:
            flow_path = config['ipv4 flow']
            action_nft = 'del_filter'
        for route in flow_path:
            #nft_cmd = f'sudo nft add rule ip {table} {chain}' if action_nft == 'add_filter' else \
            #    f'sudo nft delete rule ip {table} {chain}'
            nft_cmd = ''
            flow_route = {}
            # Allow only drop for flowspec as we use it as PoC
            flow_route['action'] = ' counter drop'
            flow_route['action_nft'] = action_nft
            #print(f'\nFlowRoute is: {route}')
            if route.get('protocol'):
                proto = route['protocol']
                flow_route['proto'] = proto
                #nft_cmd += f' {proto[0]}'
                #print(f'PROTO: {proto}')

            if route.get('destination-ipv4'):
                destination_ip = route['destination-ipv4']
                flow_route['destination_ip'] = destination_ip
                nft_cmd += f' ip daddr {destination_ip[0]}'
                #print(f'DEST_IP: {destination_ip}')
            if route.get('port'):
                port = route['port']
                flow_route['port'] = port
                # Port means src or destination port
                # Maybe it is impossible with one nft rule
                #nft_cmd += f' port {port[0]}'

            if route.get('destination-port'):
                destination_port = route.get('destination-port')
                flow_route['destination_port'] = destination_port
                nft_cmd += f' {proto[0]} dport {destination_port[0]}'
                #print(f'DEST_PORT: {destination_port}')
            if route.get('source-ipv4'):
                source_ip = route.get('source-ipv4')
                flow_route['source_ip'] = source_ip
                nft_cmd += f' ip saddr {source_ip[0]}'
                #print(f'SOURCE_IP: {source_ip}')
            if route.get('source-port'):
                source_port = route.get('source-port')
                flow_route['source_port'] = source_port
                nft_cmd += f' {proto[0]} sport {source_port[0]}'
            if route.get('packet-length'):
                packet_length = route.get('packet-length')
                flow_route['packet_length'] = packet_length
                nft_cmd += f' ip length {packet_length[0]}'
                #print(f'SRC_PORT: {source_port}')
            nft_cmd += flow_route.get('action')
            print('\nFlow-route dict: ')
            pprint(flow_route)
            pattern_del = '='
            nft_cmd = re.sub(fr'{pattern_del}', '', nft_cmd)
            #print(f'NFT_CMD: {nft_cmd}')
            nft_add_rule(table, chain, nft_cmd) if action_nft == 'add_filter' else nft_del_rule(table, chain, nft_cmd)

