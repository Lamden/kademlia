from vmnet.test.base import BaseNetworkTestCase
import unittest
import time

def run_node():
    import asyncio, zmq.asyncio
    from kademlia.discovery.ddd import discover, _listen_for_crawlers
    loop = asyncio.get_event_loop()
    ctx = zmq.asyncio.Context()
    _listen_for_crawlers(ctx)
    ips = loop.run_until_complete(discover(ctx, 'test'))
    loop.run_forever()

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
