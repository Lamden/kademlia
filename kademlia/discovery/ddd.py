"""
    Scans ip addresses for the decentralized dynamic discover procedure
"""


from kademlia.discovery.ip import *
from kademlia.discovery.msg import *
from kademlia.logger import get_logger
import os, json, uuid, resource, socket, select, asyncio, time

SOCKET_LIMIT = 2500
log = get_logger(__name__)
resource.setrlimit(resource.RLIMIT_NOFILE, (SOCKET_LIMIT, SOCKET_LIMIT))

class Discovery:
    available_ips = {}
    subnets = {}
    max_wait = 3
    min_bootstrap_nodes = 3
    max_tasks = 10000
    def getavailable_ips(self):
        return self.available_ips

    async def discover(self, mode, return_asap=True):
        ips = {}
        if mode in ['test', 'local']:
            host = os.getenv('HOST_IP', '127.0.0.1')
            hostname = 'virtual_network' if os.getenv('HOST_IP') else 'localhost'
            ips[hostname] = [decimal_to_ip(d) for d in range(*get_local_range(host))]
            self.subnets[get_subnet(host)] = {'area': hostname, 'count': 0}
        else:
            public_ip = get_public_ip()
            if mode == 'neighborhood':
                for area in get_region_range(public_ip):
                    ip, city = area.split(',')
                    ips[city] = [decimal_to_ip(d) for d in range(*get_local_range(ip))]
                    self.subnets[get_subnet(ip)] = {'area': city, 'count': 0}
        log.debug('Scanning {} ...'.format(mode))
        self.status_update(status='scan_start', msg='Starting scan in "{}" mode...'.format(mode))
        self.sem = asyncio.Semaphore(self.max_tasks)
        self.return_asap = return_asap
        all_ips = []
        for city in ips: all_ips += ips[city]
        try: await asyncio.wait_for(self.scan_all(all_ips), timeout=self.max_wait)
        except: pass
        log.debug('{}/{} IP addresses in total a of {} subnets of {} regions are available'.format(len(self.available_ips.keys()), len(all_ips), len(self.subnets.keys()), len(ips.keys())))
        log.debug(self.available_ips)
        self.status_update(status='scan_done', msg='Finished!', active_ips=self.available_ips)
        return self.available_ips

    async def fetch(self, ip):
        self.udp_sock.sendto(compose_msg(['discover', os.getenv('HOST_IP', '127.0.0.1')]), (ip, self.crawler_port))
        await asyncio.sleep(self.max_wait)

    async def bound_fetch(self, ip):
        async with self.sem:
            return await self.fetch(ip)

    async def scan_all(self, ips):
        tasks = [asyncio.ensure_future(self.bound_fetch(ip)) for ip in ips]
        self.futures = asyncio.ensure_future(asyncio.gather(*tasks))
        return await self.futures

    def listen_for_crawlers(self):
        self.udp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.udp_sock.setblocking(False)
        self.udp_sock_server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.udp_sock_server.bind(('', self.crawler_port))
        self.udp_sock_server.setblocking(False)
        asyncio.ensure_future(self.listen())

    async def listen(self):
        log.debug('Listening to the world on port {}...'.format(self.crawler_port))
        while True:
            data = await self.loop.sock_recv(self.udp_sock_server, 1024)
            msg_type, payload = decode_msg(data)
            addr = (payload[0], self.crawler_port)
            if msg_type == 'discover':
                self.udp_sock_server.sendto(compose_msg(['ack', os.getenv('HOST_IP', '127.0.0.1')]), addr)
            elif msg_type == 'ack':
                subnet = get_subnet(addr[0])
                if self.subnets.get(subnet):
                    self.available_ips[addr[0]] = int(time.time())
                    self.subnets[subnet]['count'] += 1
                    if len(self.available_ips) >= self.min_bootstrap_nodes and self.return_asap:
                        self.futures.cancel()
