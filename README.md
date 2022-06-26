# PoC of parse exabgp JSON input and generate nftables firewall rules

Generate rules:
* source address
* destination address
* destination port
* source port
* proto

TODO parse other options

```
DEBUG: sudo nft -- add table ip flowspec
DEBUG: sudo nft -- add chain ip flowspec drop_flow_routes '{ type filter hook prerouting priority -300; policy accept; }'

Flow-route dict: 
{'action': ' counter drop',
 'action_nft': 'add_filter',
 'source_ip': ['192.0.2.33/32']}
DEBUG: sudo nft add rule ip flowspec drop_flow_routes  ip saddr 192.0.2.33/32 counter drop

Flow-route dict: 
{'action': ' counter drop',
 'action_nft': 'add_filter',
 'destination_ip': ['192.0.2.5/32'],
 'destination_port': ['=3128'],
 'port': ['=80'],
 'proto': ['=tcp'],
 'source_port': ['=8888']}
DEBUG: sudo nft add rule ip flowspec drop_flow_routes  ip daddr 192.0.2.5/32 tcp dport 3128 tcp sport 8888 counter drop
```

Podman:
```
podman run --detach --privileged --interactive --tty --replace  \
  --restart on-failure --name exabgp-controller \
  -v /etc/exabgp/exabgp-controller.conf:/etc/exabgp/exabgp.conf \
  -v /config/container/exabgp/test.py:/etc/exabgp/test.py  --net NET01 --ip 10.0.0.254 \
  localhost/exabgp-noautostart

```
In container (user root for nft):
```
root@dc23372924cc:/# cat /etc/exabgp/exabgp.env 
[exabgp.daemon]
user = 'root'

root@dc23372924cc:/# exabgp -d /etc/exabgp/exabgp.conf
```

DEBUG:
```
############ DEBUG_JSON: data: {'exabgp': '4.0.1', 'time': 1656258912.4709525, 'host': 'dc23372924cc', 'pid': 276, 'ppid': 3, 'counter': 3, 'type': 'update', 'neighbor': {'address': {'local': '10.0.0.254', 'peer': '10.0.0.1'}, 'asn': {'local': 65001, 'peer': 65001}, 'direction': 'receive', 'message': {'update': {'attribute': {'origin': 'igp', 'med': 0, 'local-preference': 100, 'originator-id': '10.0.0.10', 'cluster-list': ['192.168.122.14'], 'extended-community': [{'value': 9225060886715039744, 'string': 'rate-limit:0'}]}, 'announce': {'ipv4 flow': {'no-nexthop': [{'destination-ipv4': ['192.0.2.5/32'], 'string': 'flow destination-ipv4 192.0.2.5/32'}]}}}}}}
DEBUG: nft add table flowspec
15:55:12 | 276    | peer-1        |    UPDATE #1 nlri  (   7) flow destination-ipv4 192.0.2.5/32
DEBUG: nft -- add chain ip flowspec drop_flow_routes { type filter hook prerouting priority -300; policy accept; }
DEBUG: nft add rule ip flowspec drop_flow_routes  ip daddr 192.0.2.5/32 counter drop
15:55:13 | 276    | ka-outgoing-1 | receive-timer 179 second(s) left
`
```
List ruleset:
```
root@dc23372924cc:/# nft list ruleset
table ip flowspec {
    chain drop_flow_routes {
	type filter hook prerouting priority -300; policy accept;
	ip daddr 192.0.2.5 counter packets 0 bytes 0 drop
    }
}

```