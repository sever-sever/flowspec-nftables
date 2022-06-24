#!/usr/bin/env python3


import json
import re

from pprint import pprint

# Example announce dict
update = {
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

data = update
#data = withdraw

if data.get('neighbor').get('message').get('update'):
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
            nft_cmd = 'sudo nft add rule ip flowspec drop_flow_routes' if action_nft == 'add_filter' else \
                'sudo nft delete rule ip flowspec drop_flow_routes'
            flow_route = {}
            # Allow only drop for flowspec as we use it as PoC
            flow_route['action'] = ' drop'
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
                nft_cmd += f' {proto[0]} daddr {destination_ip[0]}'
                #print(f'DEST_IP: {destination_ip}')
            if route.get('port'):
                port = route['port']
                flow_route['port'] = port
                nft_cmd += f' port {port[0]}'

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
            print('\nFilter: ')
            pprint(flow_route)
            pattern_del = '='
            nft_cmd = re.sub(fr'{pattern_del}', '', nft_cmd)
            print(f'NFT_CMD: {nft_cmd}')


