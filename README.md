# PoC of parse exabgp JSON file and generate nftables firewall rules

Generate rules:
* source address
* destination address
* destination port
* source port
* proto

TODO parse other options

```
DEBUG: sudo nft add table ip flowspec
DEBUG: sudo nft add chain ip flowspec drop_flow_routes { type filter hook prerouting priority -300; policy accept; }

Flow-route dict: 
{'action': ' drop', 'action_nft': 'add_filter', 'source_ip': ['192.0.2.33/32']}
DEBUG: sudo nft add rule ip flowspec drop_flow_routes  ip saddr 192.0.2.33/32 drop

Flow-route dict: 
{'action': ' drop',
 'action_nft': 'add_filter',
 'destination_ip': ['192.0.2.5/32'],
 'destination_port': ['=3128'],
 'port': ['=80'],
 'proto': ['=tcp'],
 'source_port': ['=8888']}
DEBUG: sudo nft add rule ip flowspec drop_flow_routes  ip daddr 192.0.2.5/32 tcp dport 3128 tcp sport 8888 drop
```
