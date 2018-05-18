from vmnet.test.base import BaseNetworkTestCase
import unittest
import time

def run_node():
    import asyncio, zmq.asyncio, os
    from kademlia.discovery.ddd import Discovery
    from kademlia.logger import get_logger
    log = get_logger(__name__)

    class DHT(Discovery):
        def __init__(self):
            self.loop = asyncio.get_event_loop()
            self.ctx = zmq.asyncio.Context()
            self.crawler_port = os.getenv('CRAWLER_PORT', 31337)
        def status_update(self, status, msg, *args, **kwargs):
            log.debug('{} - {}'.format(status, msg))

    dht = DHT()
    dht.listen_for_crawlers()
    ips = dht.loop.run_until_complete(dht.discover('neighborhood'))
    dht.loop.run_forever()

class TestDDDHB(BaseNetworkTestCase):
    testname = 'discovery'
    compose_file = 'kademlia-nodes.yml'
    setuptime = 10
    def test_setup_server_clients(self):
        for node in ['node_{}'.format(n) for n in range(1,8)]:
            self.execute_python(node, run_node, async=True)
        time.sleep(360)

if __name__ == '__main__':
    unittest.main()
