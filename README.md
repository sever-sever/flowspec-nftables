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
## Integrate to VyOS
Add container and bgp session between ExaBGP controller and VyOS

Controller sends `nft` commands to remote host
* Download 
```
sudo mkdir -p /config/container/exabgp/
sudo mkdir -p /tmp/exabgp

sudo wget -O /tmp/exabgp/Dockerfile https://raw.githubusercontent.com/sever-sever/flowspec-nftables/main/Dockerfile
sudo wget -O /config/container/exabgp/exabgp-controller.conf https://raw.githubusercontent.com/sever-sever/flowspec-nftables/main/exabgp-controller.conf
sudo wget -O /config/container/exabgp/test.py https://github.com/sever-sever/flowspec-nftables/blob/main/test.py
sudo wget -O /config/container/exabgp/exabgp.env https://raw.githubusercontent.com/sever-sever/flowspec-nftables/main/exabgp.env

```
* Generate image (use only one command VyOS or native podman/docker)
```
generate container image exabgp-noautostart path /tmp/exabgp
podman build -t exabgp-noautostart /tmp/exabgp

```
### VyOS configuration:
```
set container name exabgp-controller cap-add 'net-admin'
set container name exabgp-controller image 'localhost/exabgp-noautostart'
set container name exabgp-controller network NET01 address '10.0.0.254'
set container name exabgp-controller volume config destination '/etc/exabgp/exabgp.conf'
set container name exabgp-controller volume config source '/config/container/exabgp/exabgp-controller.conf'
set container name exabgp-controller volume env destination '/etc/exabgp/exabgp.env'
set container name exabgp-controller volume env source '/config/container/exabgp/exabgp.env'
set container name exabgp-controller volume script destination '/etc/exabgp/test.py'
set container name exabgp-controller volume script source '/config/container/exabgp/test.py'
set container network NET01 prefix '10.0.0.0/24'
set nat source rule 100 outbound-interface 'eth0'
set nat source rule 100 source address '10.0.0.0/24'
set nat source rule 100 translation address 'masquerade'
set protocols bgp local-as '65001'
set protocols bgp neighbor 10.0.0.254 address-family ipv4-flowspec route-reflector-client
set protocols bgp neighbor 10.0.0.254 remote-as '65001'
```
* Connect to container and start exabgp in debug mode
```
connect container exabgp-controller
bash
exabgp -d /etc/exabgp/exabgp.conf

```

Receive flowspec route and check firewall rules:
```
vyos@r14:~$ sudo nft list table ip flowspec
table ip flowspec {
	chain drop_flow_routes {
		type filter hook prerouting priority raw; policy accept;
		ip daddr 192.0.2.33 ip saddr 203.0.113.1 counter packets 0 bytes 0 drop
		ip daddr 192.0.2.5 counter packets 0 bytes 0 drop
	}
}
vyos@r14:~$ 
```
