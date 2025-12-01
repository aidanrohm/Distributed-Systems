# Coordinator script
#
# Node0 = coordinator
#   - Performs 2PC across Node1 (manager for A) and Node2 (manager for B)
#   - Exposes RPC for the client:
#       run_transfer_100_scenario()
#       run_bonus_20_percent_scenario()
#
# The client can call these to trigger the transactions

from xmlrpc.server import SimpleXMLRPCServer
from xmlrpc.client import ServerProxy
import time
import uuid
import os

# This server runs on node-0
HOST = "10.128.0.2"   # node-0 internal IP
PORT = 8000           # RPC port for coordinator

# URLs of the participants (using internal IPs)
NODE1_URL = "http://10.128.0.3:8001/"   # node-1 (A)
NODE2_URL = "http://10.128.0.5:8002/"   # node-2 (B)

# All Coordinator log messages will go to this file
LOG_FILE = "log_node0_coordinator.txt"


class Coordinator:
    def __init__(self, node1_url, node2_url, log_file):
        self.pA = ServerProxy(node1_url, allow_none=True)  # Creates a remote object (participant A)
        self.pB = ServerProxy(node2_url, allow_none=True)  # Creates a remote object (participant B)
        self.log_file = log_file
        self._log("Coordinator initialized")

    # Creates a time stamped log line with [COORD] as a prefix
    # Helps digest the log as it makes it clear where the line is coming from
    # Used as a way to write to the log whenever an action is committed
    def _log(self, msg):
        ts = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        line = f"[{ts}] [COORD] {msg}"
        print(line)
        with open(self.log_file, "a") as f:
            f.write(line + "\n")

    # --------- Generic 2PC driver ---------
    # tx_type is a string like "T1_TRANSFER_100" or "T2_BONUS"
    def _two_phase_commit(self, tx_type, params=None):
        if params is None:
            params = {}

        # Generates a unique transaction ID that is used during logging
        tx_id = str(uuid.uuid4())
        self._log(f"Starting 2PC tx_id={tx_id}, type={tx_type}, params={params}")

        # Phase 1: PREPARE
        try:
            # Expects prepare to return a vote (True=yes, False=no)
            # If a network error/exception occurs, this is treated as a "no"
            vote_A = self.pA.prepare(tx_id, tx_type, params)
            self._log(f"Vote from A: {vote_A}")
        except Exception as e:
            self._log(f"Exception contacting A during prepare: {e}")
            vote_A = False

        try:
            # Expects prepare to return a vote (True=yes, False=no)
            # If a network error/exception occurs, this is treated as a "no"
            vote_B = self.pB.prepare(tx_id, tx_type, params)
            self._log(f"Vote from B: {vote_B}")
        except Exception as e:
            self._log(f"Exception contacting B during prepare: {e}")
            vote_B = False

        # Combines response from both participants
        all_yes = (vote_A and vote_B)

        # Phase 2: COMMIT or ABORT
        # Will only execute if both participant nodes vote "yes"
        if all_yes:
            self._log(f"All YES; sending COMMIT for tx_id={tx_id}")
            try:
                self.pA.commit(tx_id)
            except Exception as e:
                self._log(f"Error sending COMMIT to A: {e}")
            try:
                self.pB.commit(tx_id)
            except Exception as e:
                self._log(f"Error sending COMMIT to B: {e}")
            self._log(f"Transaction {tx_id} committed.")
            return True    # Indicating success
        else:    # Log that we are aborting in the event that one (or both) of the participants vote "no"
            self._log(f"At least one NO; sending ABORT for tx_id={tx_id}")
            try:
                self.pA.abort(tx_id)
            except Exception as e:
                self._log(f"Error sending ABORT to A: {e}")
            try:
                self.pB.abort(tx_id)
            except Exception as e:
                self._log(f"Error sending ABORT to B: {e}")
            self._log(f"Transaction {tx_id} aborted.")
            return False    # Indicating failure

    # --------- Scenario helpers exposed to client ---------
    
    def initialize_balances(self, a_value, b_value):
        # Based on parameters set by assignment
        self._log(f"Initializing balances: A={a_value}, B={b_value}")
        self.pA.set_balance(int(a_value))
        self.pB.set_balance(int(b_value))
        return True

    def run_transfer_100(self):
        """
        Transaction 1: transfer 100 from A to B.
        """
        self._log("Client requested: run_transfer_100")
        success = self._two_phase_commit("T1_TRANSFER_100")
        return success    # Returns True/False to the client depending on whether or not it is successful

    def run_bonus_20_percent(self):
        """
        Transaction 2: add 20% of A's current balance to both A and B.
        """
        self._log("Client requested: run_bonus_20_percent")
        
        try:
            a_balance = self.pA.get_balance()
        except Exception as e:
            self._log(f"Failed to read A balance: {e}")
            return False

        bonus = int(0.2 * a_balance)
        self._log(f"A balance={a_balance}, bonus=0.2*A={bonus}")
        params = {"bonus": bonus}
        success = self._two_phase_commit("T2_BONUS", params)
        return success    # Returns True/False to the client depending on whether or not it is successful

    # Lets the client ask the coordinator for both account balances in one call
    def get_balances(self):
        try:
            a_balance = self.pA.get_balance()
            b_balance = self.pB.get_balance()
        except Exception as e:
            self._log(f"Error reading balances: {e}")
            return {"error": str(e)}
        self._log(f"get_balances -> A={a_balance}, B={b_balance}")
        return {"A": a_balance, "B": b_balance}


def main():
    # Create log file if missing
    if not os.path.exists(LOG_FILE):
        with open(LOG_FILE, "w") as f:
            f.write("")

    # Creates the XML-RPC server bound to the HOST and PORT
    server = SimpleXMLRPCServer((HOST, PORT), allow_none=True, logRequests=True)
    coord = Coordinator(NODE1_URL, NODE2_URL, LOG_FILE)    # Instantiate coordinator object
    server.register_instance(coord)                        # Makes all public methods on coord callable
    
    # Startup message and looping
    print(f"Coordinator (node0) listening on {HOST}:{PORT} ...")
    server.serve_forever()


if __name__ == "__main__":
    main()
