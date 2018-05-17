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

class Discovery:
    _available_ips = {}
    def get_available_ips(self):
        return self._available_ips

    async def discover(self, mode):
        ips = {}
        if mode == 'test':
            host = os.getenv('HOST_IP', '127.0.0.1')
            ips['virtual_network'] = [decimal_to_ip(d) for d in range(*get_local_range(host))]
        else:
            public_ip = get_public_ip()
            if mode == 'local':
                ips['localhost'] = [(decimal_to_ip(d), 'localhost') for d in range(*get_local_range(public_ip))]
            elif mode == 'neighborhood':
                for area in get_region_range(public_ip):
                    ip, city = area.split(',')
                    ips[city] = [decimal_to_ip(d) for d in range(*get_local_range(ip))]
        log.debug('Scanning {} ...'.format(mode))
        self.status_update(status='scan_start', msg='Starting scan in "{}" mode...'.format(mode))
        results = []
        self.sem = asyncio.Semaphore(10000)
        for city in ips:
            res = await self.scan_all(ips[city])
            res = list(set([r for r in res if r != None]))
            results += res
            self.status_update(status='scan_processing', msg='Scanned: {} ({}/255 available)'.format(city, len(res)))
            self._available_ips[city] = { 'count': len(res), 'ips': res }
        log.debug('Done.')
        self.status_update(status='scan_done', msg='Finished!', active_ips=results)
        return results

    async def fetch(self, s, ip):
        url = "tcp://{}:{}".format(ip, self.crawler_port)
        s.connect(url)
        s.send(compose_msg('discover'))
        await s.recv()
        return ip

    async def bound_fetch(self, ip):
        async with self.sem:
            sock = self.ctx.socket(zmq.REQ)
            sock.linger = 0
            result = None
            try: result = await asyncio.wait_for(self.fetch(sock, ip), timeout=0.5)
            except asyncio.TimeoutError: pass
            sock.close()
            return result

    async def scan_all(self, ips):
        tasks = [asyncio.ensure_future(self.bound_fetch(ip)) for ip in ips]
        return await asyncio.ensure_future(asyncio.gather(*tasks))

    def listen_for_crawlers(self):
        self.sock = self.ctx.socket(zmq.REP)
        self.sock.bind("tcp://*:{}".format(self.crawler_port))
        asyncio.ensure_future(self.listen(self.sock))

    async def listen(self, socket):
        log.debug('Listening to the world on port {}...'.format(self.crawler_port))
        while True:
            msg = await socket.recv_multipart()
            msg_type, data = decode_msg(msg)
            if data:
                log.debug("Received - {}: {}".format(msg_type, data))
            socket.send(compose_msg())
