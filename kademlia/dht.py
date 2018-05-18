from kademlia.discovery.ddd import Discovery
from kademlia.network import Network
from kademlia.utils import digest
from kademlia.logger import get_logger
from queue import Queue
import os, sys, uuid, time, threading, uuid, asyncio, random, zmq.asyncio, warnings, zmq, logging
from multiprocessing import Process

log = get_logger(__name__)

class DHT(Discovery):
    def __init__(self, node_id=None, mode='neighborhood', cmd_cli=False, block=True, loop=None, ctx=None, *args, **kwargs):
        self.loop = loop if loop else asyncio.get_event_loop()
        asyncio.set_event_loop(self.loop)
        self.crawler_port = os.getenv('CRAWLER_PORT', 31337)
        self.ctx = ctx if ctx else zmq.asyncio.Context()
        self.listen_for_crawlers()
        self.ips = self.loop.run_until_complete(self.discover(mode))
        if len(self.ips) == 0: self.ips.append(os.getenv('HOST_IP', '127.0.0.1'))
        self.network_port = os.getenv('NETWORK_PORT', 5678)
        self.network = Network(node_id=node_id, loop=self.loop, dht=self, *args, **kwargs)
        self.network.listen(self.network_port)

        self.join_network()

        if cmd_cli:
            self.q = Queue()
            self.cli_thread = threading.Thread(name='cmd_cli', target=DHT.command_line_interface, args=(self.q,))
            self.cli_thread.start()
            asyncio.ensure_future(self.recv_cli())

        if block:
            log.debug('Server started and blocking...')
            self.loop.run_forever()

    def _status_update(self, *args, **kwargs):
        if not hasattr(self, 'status_update'):
            log.warn('status_update() not implemented. One can implement this function to capture any status updates')
        else:
            self.status_update(*args, **kwargs)

    @staticmethod
    def command_line_interface(q):
        """
            Serves as the local command line interface to set or get values in
            the network.
        """
        while True:
            command = input("Enter command (e.g.: <get/set> <key> <value>):\n")
            args = list(filter(None, command.strip().split(' ')))
            if len(args) != 0: q.put(args)

    async def recv_cli(self):
        print("\n STARTING READING FROM CLI QUEUE \n")
        while True:
            try:
                cmd = self.q.get_nowait()
                print("\n\n EXECUTING CMD: {}\n\n".format(cmd))
                if cmd[0] == 'get':
                    await self.get_value(cmd[1])
                elif cmd[0] == 'set':
                    await self.set_value(cmd[1], cmd[2])
                else:
                    warnings.warn("Unknown cmd arg: {}".format(cmd[0]))
            except Exception as e:
                pass
            await asyncio.sleep(0.5)

    async def set_value(self, key, val):
        log.debug('setting {} to {}...'.format(key, val))
        output = await asyncio.ensure_future(self.network.set(key, val))
        log.debug('done!')

    async def get_value(self, key):
        log.debug('getting {}...'.format(key))
        res = await asyncio.ensure_future(self.network.get(key))
        log.debug('res={}'.format(res))
        return res

    def join_network(self):
        log.debug('Joining network: {}'.format(self.ips))
        try: self.loop.run_until_complete(self.network.bootstrap([(ip, self.network_port) for ip in self.ips]))
        except: pass

if __name__ == '__main__':
    server = DHT(node_id='vk_{}'.format(os.getenv('HOST_IP', '127.0.0.1')), block=True, cmd_cli=True)
