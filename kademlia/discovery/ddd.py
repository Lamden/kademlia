"""
    Scans ip addresses for the decentralized dynamic discover procedure
"""


from kademlia.discovery.ip import *
from kademlia.discovery.msg import *
from kademlia.logger import get_logger
import zmq.asyncio
import os, json, uuid, zmq, resource, socket, select, asyncio

SOCKET_LIMIT = 2500
log = get_logger(__name__)
resource.setrlimit(resource.RLIMIT_NOFILE, (SOCKET_LIMIT, SOCKET_LIMIT))
port = os.getenv('CRAWLER_PORT', 31337)

async def discover(ctx, mode):
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
    sem = asyncio.Semaphore(10000)
    for h in ips:
        results += await scan_all(ctx, sem, ips[h])
    results = list(set([r for r in results if r != None]))
    log.debug('Done.')
    return results

async def fetch(s, ip):
    url = "tcp://{}:{}".format(ip, port)
    s.connect(url)
    s.send(compose_msg('discover'))
    await s.recv()
    return ip

async def bound_fetch(ctx, sem, ip):
    async with sem:
        sock = ctx.socket(zmq.REQ)
        sock.linger = 0
        result = None
        try: result = await asyncio.wait_for(fetch(sock, ip), timeout=0.5)
        except asyncio.TimeoutError: pass
        sock.close()
        return result

async def scan_all(ctx, sem, ips):
    loop = asyncio.get_event_loop()
    tasks = [asyncio.ensure_future(bound_fetch(ctx, sem, ip)) for ip in ips]
    return await asyncio.ensure_future(asyncio.gather(*tasks))

def _listen_for_crawlers(ctx):
    sock = ctx.socket(zmq.REP)
    asyncio.ensure_future(_listen(sock))

async def _listen(socket):
    socket.bind("tcp://*:{}".format(port))
    log.debug('Listening to the world on port {}...'.format(port))
    while True:
        msg = await socket.recv_multipart()
        msg_type, data = decode_msg(msg)
        if data:
            log.debug("Received - {}: {}".format(msg_type, data))
        socket.send(compose_msg())

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='Do da decentralized dynamic discovery dance!')
    parser.add_argument('--discovery_mode', help='local, neighborhood, popular, predictive', required=True)
    args = parser.parse_args()
    loop = asyncio.get_event_loop()
    ips = loop.run_until_complete(discover(zmq.asyncio.Context(), args.discovery_mode))
    print(ips)
