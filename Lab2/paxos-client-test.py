import pickle
from multiprocessing.connection import Client

class RPCProxy:
    def __init__(self, connection):
        self._connection = connection

    def __getattr__(self, name):
        def do_rpc(*args, **kwargs):
            # Send (func_name, args, kwargs) as a pickled bytes object
            self._connection.send(pickle.dumps((name, args, kwargs)))
            # Receive pickled result
            result = pickle.loads(self._connection.recv())
            if isinstance(result, Exception):
                raise result
            return result
        return do_rpc


if __name__ == "__main__":
    # Connect this client to ONE node in the cluster.
    # You can change the IP to 10.128.0.2 / .3 / .5 to test different proposers.
    c = Client(('34.63.196.172', 17000), authkey=b'peekaboo')

    proxy = RPCProxy(c)

    # Submit a single value into the distributed file
    print(proxy.SubmitValue("Hello from clientA"))

    # Read back the value stored on that node
    print("Current value on this node:", proxy.get_value())

    c.close()
