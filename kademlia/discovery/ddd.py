"""
    Scans ip addresses for the decentralized dynamic discover procedure
"""


from kademlia.discovery.ip import *
from kademlia.discovery.msg import *
from kademlia.logger import get_logger
import os
import json
import uuid
import zmq
import resource

SOCKET_LIMIT = 2500
log = get_logger(__name__)
resource.setrlimit(resource.RLIMIT_NOFILE, (SOCKET_LIMIT, SOCKET_LIMIT))
port = os.getenv('CRAWLER_PORT', 31337)
ctx = zmq.Context()

async def discover(mode):
    ips = {}
    if mode == 'test':
        host = os.getenv('HOST_IP', '127.0.0.1')
        ips[host] = [decimal_to_ip(d) for d in range(*get_local_range(host))]
    else:
        public_ip = get_public_ip()
        if mode == 'local':
            ips['localhost'] = [decimal_to_ip(d) for d in range(*get_local_range(public_ip))]
        elif mode == 'neighborhood':
            for ip in get_region_range(public_ip):
                ips[ip] = [decimal_to_ip(d) for d in range(*get_local_range(ip))]
    log.debug('Scanning {} ...'.format(mode))
    results = []
    for h in ips:
        results += scan_all(ips[h])
    log.debug('Done.')
    return results

def scan_all(ips, poll_time=100):
    sockets = []
    results = []
    poller = zmq.Poller()
    for ip in ips:
        url = "tcp://{}:{}".format(ip, port)
        sock = ctx.socket(zmq.REQ)
        sock.linger = 0
        sock.connect(url)
        sockets.append({
            'socket': sock,
            'ip':ip
        })
        sock.send(compose_msg('discover'), zmq.NOBLOCK)
        poller.register(sock, zmq.POLLIN)

    evts = dict(poller.poll(poll_time))
    for s in sockets:
        sock = s['socket']
        ip = s['ip']
        if evts.get(sock):
            log.debug("{} is online".format(ip))
            results.append(ip)
        poller.unregister(sock)
    return results

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='Do da decentralized dynamic discovery dance!')
    parser.add_argument('--discovery_mode', help='local, neighborhood, popular, predictive', required=True)
    args = parser.parse_args()
    discover(args.discovery_mode)
