# PoC of parse exabgp JSON file and generate nftables firewall rules

```
Filter:
{'action': ' drop', 'action_nft': 'add_filter', 'source_ip': ['192.0.2.33/32']}
NFT_CMD: sudo nft add rule ip flowspec drop_flow_routes ip saddr 192.0.2.33/32 drop

Filter:
{'action': ' drop',
 'action_nft': 'add_filter',
 'destination_ip': ['192.0.2.5/32'],
 'destination_port': ['=3128'],
 'port': ['=80'],
 'proto': ['=tcp'],
 'source_port': ['=8888']}
NFT_CMD: sudo nft add rule ip flowspec drop_flow_routes ip daddr 192.0.2.5/32 tcp daddr 192.0.2.5/32 port 80 tcp dport 3128 tcp sport 8888 drop
```
