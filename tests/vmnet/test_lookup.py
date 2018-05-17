from vmnet.test.base import BaseNetworkTestCase
import unittest
import time, os

def run_lookup_node():
    from kademlia.dht import DHT
    import time, os, asyncio, threading
    loop = asyncio.get_event_loop()
    asyncio.set_event_loop(loop)
    node = DHT(node_id='vk_{}'.format(os.getenv('HOST_IP')), mode='test', block=False, cmd_cli=False)
    async def delay_run(t):
        await asyncio.sleep(t)
        return await node.network.lookup_ip('vk_172.29.5.3')
    result = asyncio.ensure_future(delay_run(8))
    loop.run_forever()

def run_node():
    from kademlia.dht import DHT
    import time, os, asyncio
    loop = asyncio.get_event_loop()
    asyncio.set_event_loop(loop)
    node = DHT(node_id='vk_{}'.format(os.getenv('HOST_IP')), mode='test', block=False, cmd_cli=False)
    loop.run_forever()

class TestDDDHB(BaseNetworkTestCase):
    testname = 'lookup'
    compose_file = 'kademlia-nodes.yml'
    setuptime = 10
    def test_setup_server_clients(self):
        self.execute_python('node_1', run_lookup_node, async=True)
        time.sleep(3)
        for node in ['node_{}'.format(n) for n in range(2,13)]:
            self.execute_python(node, run_node, async=True)
        time.sleep(13)
        os.system('docker kill node_4')
        time.sleep(360)

if __name__ == '__main__':
    unittest.main()
