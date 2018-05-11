from kademlia.discovery.msg import *
from kademlia.discovery.ip import *
from kademlia.discovery.ddd import *
from kademlia.network import Network
from kademlia.utils import digest
from kademlia.logger import get_logger
from queue import Queue
import os, sys, uuid, time, threading, uuid, asyncio, random, zmq.asyncio, warnings, zmq, logging
from zmq.utils.monitor import recv_monitor_message

log = get_logger(__name__)
loop = asyncio.get_event_loop()
asyncio.set_event_loop(loop)

class DHT:
    def __init__(self, node_id=None, mode='neighborhood', rediscover_interval=10, cmd_cli=False, block=True):
        self.discovery_mode = mode
        self.rediscover_interval = rediscover_interval
        self.crawler_port = os.getenv('CRAWLER_PORT', 31337)

        self.listen_for_crawlers()
        self.ips = loop.run_until_complete(discover(self.discovery_mode))

        self.network_port = os.getenv('NETWORK_PORT', 5678)
        self.network = Network(node_id=node_id)
        self.network.listen(self.network_port)

        self.join_network()

        if cmd_cli:
            self.q = Queue()
            self.cli_thread = threading.Thread(name='cmd_cli', target=Server.command_line_interface, args=(self.q,))
            self.cli_thread.start()
            asyncio.ensure_future(self.recv_cli())

        if block:
            log.debug('Server started and blocking...')
            loop.run_forever()

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
        try:
            self.ips.append(os.getenv('HOST_IP', '127.0.0.1'))
            loop.run_until_complete(self.network.bootstrap([(ip, self.network_port) for ip in self.ips]))
        except: pass

    def listen_for_crawlers(self):
        port = self.crawler_port
        self.ctx = ctx = zmq.asyncio.Context()
        self.sock = sock = ctx.socket(zmq.REP)
        sock.bind("tcp://*:{}".format(port))
        log.debug('Listening to the world on port {}...'.format(port))
        asyncio.ensure_future(self.listen(sock))

    async def listen(self, socket):
        while True:
            msg = await socket.recv_multipart()
            msg_type, data = decode_msg(msg)
            if data:
                log.debug("Received - {}: {}".format(msg_type, data))
            socket.send(compose_msg())

if __name__ == '__main__':
    server = DHT(node_id='vk_{}'.format(os.getenv('HOST_IP', '127.0.0.1')), block=True, cmd_cli=True)
