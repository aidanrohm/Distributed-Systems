import pickle
import os
import time
import random
from multiprocessing.connection import Listener, Client
from threading import Thread

# ---------- Generic RPC handler (unchanged pattern) ----------

class RPCHandler:
    def __init__(self):
        self._functions = { }

    def register_function(self, func):
        self._functions[func.__name__] = func

    def handle_connection(self, connection):
        try:
            while True:
                # Receive a message (already unpickled once by connection)
                func_name, args, kwargs = pickle.loads(connection.recv())
                # Run the RPC and send a response
                try:
                    r = self._functions[func_name](*args, **kwargs)
                    connection.send(pickle.dumps(r))
                except Exception as e:
                    connection.send(pickle.dumps(e))
        except EOFError:
            pass

# Server Nodes 
# Adjust these constants for each node in your cluster.
# Example:
#   Node 1: NODE_ID = 1, NODE_INDEX = 0
#   Node 2: NODE_ID = 2, NODE_INDEX = 1
#   Node 3: NODE_ID = 3, NODE_INDEX = 2

NODE_ID = 3          # CHANGE per node (1, 2, or 3)
NODE_INDEX = NODE_ID - 1

# All three node addresses in the cluster (from Lab-1).
# Update these to match your VM IPs.
ALL_NODES = [
    ('10.128.0.2', 17000),
    ('10.128.0.3', 17000),
    ('10.128.0.5', 17000),
]

AUTHKEY = b'peekaboo'
FILE_NAME = "CISC5597"   # replicated file name (one per node)
MAJORITY = 2             # for 3 nodes

# Paxos per-node state
promised_n = None        # highest proposal number promised
accepted_n = None        # highest proposal number accepted
accepted_value = None    # value associated with accepted_n

# Local proposal counter for this node (used when acting as proposer)
proposal_counter = 0

#File Creation
def _init_file():
    """Ensure the replicated file exists."""
    if not os.path.exists(FILE_NAME):
        with open(FILE_NAME, "w") as f:
            f.write("")


_init_file()

#File write
def _write_file(value):
    """Write the chosen value into this node's local replica."""
    with open(FILE_NAME, "w") as f:
        f.write(str(value))


def get_value():
    """Return the current value stored in this node's replica."""
    global accepted_value
    if accepted_value is not None:
        return accepted_value
    try:
        with open(FILE_NAME, "r") as f:
            data = f.read()
            return data if data != "" else None
    except FileNotFoundError:
        return None


def _next_proposal_number():
    """
    Generate a unique proposal number for this node.
    Simple scheme: (local_counter * 10) + NODE_ID
    so different nodes don't collide.
    """
    global proposal_counter
    proposal_counter += 1
    return proposal_counter * 10 + NODE_ID


def _get_peer_addresses():
    """Return addresses of the other two nodes."""
    return [addr for i, addr in enumerate(ALL_NODES) if i != NODE_INDEX]


def _call_remote(addr, func_name, *args, **kwargs):
    """
    Very small, direct RPC client for server-to-server calls,
    using the same pickle protocol as client.py.
    """
    c = Client(addr, authkey=AUTHKEY)
    try:
        # Send (func_name, args, kwargs) as a pickled bytes object
        c.send(pickle.dumps((func_name, args, kwargs)))
        # Receive pickled result
        result = pickle.loads(c.recv())
        if isinstance(result, Exception):
            raise result
        return result
    finally:
        c.close()

# Paxos RPCs: prepare & accept

def prepare(n):
    """
    Paxos Phase 1: prepare(n)
    Returns:
      ("promise", accepted_n, accepted_value) on success
      ("reject", promised_n) on failure
    """
    global promised_n, accepted_n, accepted_value
    if promised_n is None or n > promised_n:
        promised_n = n
        return ("promise", accepted_n, accepted_value)
    else:
        return ("reject", promised_n)


def accept(n, v):
    """
    Paxos Phase 2: accept(n, v)
    Returns:
      ("accepted", n) on success
      ("reject", promised_n) on failure
    """
    global promised_n, accepted_n, accepted_value
    if promised_n is None or n >= promised_n:
        promised_n = n
        accepted_n = n
        accepted_value = v
        _write_file(v)
        return ("accepted", n)
    else:
        return ("reject", promised_n)

# Client-facing RPC: SubmitValue 

def SubmitValue(value):
    """
    Client entry point.
    This node acts as a proposer and runs Basic Paxos
    to choose a value for the replicated file.
    """

    # Random delay to help simulate races between two proposers
    # when you run two clients in parallel.
    time.sleep(random.uniform(0, 2))

    n = _next_proposal_number()

    # Phase 1: Prepare
    promises = []
    highest_accepted_n = None
    highest_accepted_val = None

    # First, talk to self directly
    responses = []
    responses.append(prepare(n))

    # Then talk to other nodes via RPC
    for addr in _get_peer_addresses():
        try:
            resp = _call_remote(addr, "prepare", n)
            responses.append(resp)
        except Exception:
            # Treat RPC failure as no response
            pass

    for resp in responses:
        if resp[0] == "promise":
            _, acc_n, acc_val = resp
            promises.append(resp)
            if acc_n is not None and (highest_accepted_n is None or acc_n > highest_accepted_n):
                highest_accepted_n = acc_n
                highest_accepted_val = acc_val

    if len(promises) < MAJORITY:
        return f"Proposal Num: {proposal_counter}, SubmitValue FAILED in Phase 1 (only {len(promises)} promises)."

    # If any acceptor has already accepted a value, we must propose that value
    if highest_accepted_val is not None:
        v_to_propose = highest_accepted_val
    else:
        v_to_propose = value

    # Phase 2: Accept
    accepts = 0

    # Self
    resp = accept(n, v_to_propose)
    if resp[0] == "accepted":
        accepts += 1

    # Others
    for addr in _get_peer_addresses():
        try:
            resp = _call_remote(addr, "accept", n, v_to_propose)
            if resp[0] == "accepted":
                accepts += 1
        except Exception:
            pass

    if accepts >= MAJORITY:
        return f"Proposal Num: {proposal_counter}, SubmitValue SUCCEEDED. Chosen value = {v_to_propose}"
    else:
        return f"Proposal Num: {proposal_counter}, SubmitValue FAILED in Phase 2 (only {accepts} accepts)."

# Original RPC server
def rpc_server(handler, address, authkey):
    sock = Listener(address, authkey=authkey)
    while True:
        client = sock.accept()
        t = Thread(target=handler.handle_connection, args=(client,))
        t.daemon = True
        t.start()

# Register with a handler and additional Paxos-related functions 
handler = RPCHandler()
handler.register_function(prepare)
handler.register_function(accept)
handler.register_function(SubmitValue)
handler.register_function(get_value)

# Run the server
if __name__ == "__main__":
    rpc_server(handler, ('0.0.0.0', 17000), authkey=AUTHKEY)
