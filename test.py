#!/usr/bin/env python3

# Copyright (C) 2022 Viacheslav Hletenko
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 2 or later as
# published by the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import json
import re
import subprocess
import sys

from sys import stdin
from pprint import pprint


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
    print(f'NON_ZERO_STATUS: {rc}, command: {response.stderr}', file=sys.stderr)
    return rc, response.stderr


def nft_add_table(name='flowspec'):
    print(f'DEBUG: nft add table {name}', file=sys.stderr)
    run_rc(f'nft add table ip {name}')


def nft_add_chain(chain_name, table_name, hook='prerouting', priority='-300'):
    print(f"DEBUG: nft -- add chain ip {table_name} {chain_name} "
          f"{{ type filter hook {hook} priority {priority}; policy accept; }}", file=sys.stderr)
    run_rc(f"nft -- add chain ip {table_name} {chain_name} "
           f"{{ type filter hook {hook} priority {priority}; policy accept; }}")


def nft_add_rule(table_name, chain_name, command=''):
    print(f'DEBUG: nft add rule ip {table_name} {chain_name} {command}', file=sys.stderr)
    run_rc(f'nft add rule ip {table_name} {chain_name} {command}')


def nft_del_rule(table_name, chain_name, command=''):
    print(f'DEBUG: nft delete rule ip {table_name} {chain_name} {command}', file=sys.stderr)
    run_rc(f'nft delete rule ip {table_name} {chain_name} {command}')



while True:
    line = sys.stdin.readline().strip()
    data = json.loads(line)

    if data.get('neighbor', {}).get('message', {}).get('update', {}):
        print(f'############ DEBUG_JSON: data: {data}', file=sys.stderr)

        nft_add_table(table)
        nft_add_chain('drop_flow_routes', table)
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
                nft_cmd = ''
                flow_route = {}
                # Allow only drop for flowspec as we use it as PoC
                flow_route['action'] = ' counter drop'
                flow_route['action_nft'] = action_nft
                if route.get('protocol'):
                    proto = route['protocol']
                    flow_route['proto'] = proto
                    #nft_cmd += f' {proto[0]}'

                if route.get('destination-ipv4'):
                    destination_ip = route['destination-ipv4']
                    flow_route['destination_ip'] = destination_ip
                    nft_cmd += f' ip daddr {destination_ip[0]}'
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
                if route.get('source-ipv4'):
                    source_ip = route.get('source-ipv4')
                    flow_route['source_ip'] = source_ip
                    nft_cmd += f' ip saddr {source_ip[0]}'
                if route.get('source-port'):
                    source_port = route.get('source-port')
                    flow_route['source_port'] = source_port
                    nft_cmd += f' {proto[0]} sport {source_port[0]}'
                if route.get('packet-length'):
                    packet_length = route.get('packet-length')
                    flow_route['packet_length'] = packet_length
                    nft_cmd += f' ip length {packet_length[0]}'
                nft_cmd += flow_route.get('action')
                print('\nFlow-route dict: ')
                pprint(flow_route)
                pattern_del = '='
                nft_cmd = re.sub(fr'{pattern_del}', '', nft_cmd)
                nft_add_rule(table, chain, nft_cmd) if action_nft == 'add_filter' else nft_del_rule(table, chain, nft_cmd)
