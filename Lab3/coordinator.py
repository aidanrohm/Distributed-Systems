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

HOST = "10.128.0.2"     # Listening on all interfaces on Node0
PORT = 8000             # Coordinator's RPC port

# --- CHANGE THESE VALUES TO MATCH THE STRUCTURE OF YOUR SERVER'S IPs ---
NODE1_URL = "http://10.128.0.3:8001/"   # Node1 (manager for account A)
NODE2_URL = "http://10.128.0.5:8002/"   # Node2 (manager for account B)

LOG_FILE = "log_coordinator.txt"

class Coordinator:
    def __init__(self, node1_url, node2_url, log_file):
        self.pA = ServerProxy(node1_url, allow_none=True)   # Participant A
        self.pB = ServerProxy(node2_url, allow_none=True)   # Participant B
        self.log_file = log_file
        self._log("Coordinator initialized!")

    def _log(self, msg):
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        line = f"[{timestamp}] [COORD] {msg}"
        print(line)
        with open(self.log_file, "a") as f:
            f.write(line + "\n")

    # ----------- Generic 2PC Driver -----------

    def _two_phase_commit(self, tc_tyoe, params=None):
        """
        Generic 2PC.
        Params is a dictionary passed to participants' prepare()
        tx_type: 'T1_TRANSFER_100' or 'T2_BONUS'
        """

        if params is None:
            params = {}

        tx+id = str(uuid.uuid4())
        self.log(f"Starting 2PC tx_id={tx_id}, type={tx_type}, params={params}")

        # Phase 1 : Prepare
        try:
            vote_A: self.pA.prepare(tx_id, tx_type, params)
            self._log(f"Vote from A: {vote_A}")
        except Exception as e:
            self._log(f"Exception contacting participant A during prepare: {e}")
            vote_A = False

        try:
            vote_B = self.pB.prepare(tx_id, tx_type, params)
            self._log(f"Vote from B: {vote_B}")
        except Exception as e:
            self._log(f"Exception contacting participant B during prepare: {e}")
            vote_B = False

        all_yes = (vote_A and vote_B)

        # Phase 2 : Commit or Abort
        if all_yes:
            self._log(f"All participants voted YES; sending COMMIT for tx_id={tx_id}")
            try:
                self.pA.commit(tx_id)
            except Exception as e:
                self._log(f"Error sending COMMIT to A: {e}")
            try:
                self.pB.commit(tx_id)
            except Exception as e:
                self._log(f"Error sending COMMIT to B: {e}")
            self._log(f"Transaction {tx_id} committed.")
            return True
        else:
            self._log(f"At least one participant voted NO; sending ABORT for tx_id={tx_id}")
            try:
                self.pA.abort(tx_id)
            except Exception as e:
                self._log(f"Error sending ABORT to A: {e}")
            try:
                self.pB.abort(tx_id)
            except Exception as e:
                self._log(f"Error sending ABORT to B: {e}")
            self._log(f"Transaction {tx_id} aborted.")
            return False

    # --------- Scenario helpers called by the client ---------

    def initialize_balances(self, a_value, b_value):
        """Helper: set initial balances for A and B."""
        self._log(f"Initializing balances: A={a_value}, B={b_value}")
        self.pA.set_balance(int(a_value))
        self.pB.set_balance(int(b_value))
        return True

    def run_transfer_100(self):
        """
        Transaction 1: Transfer 100 dollars from A to B.
        This assumes the semantics:
          A := A - 100
          B := B + 100
        The participants encode that logic in their prepare() methods.
        """
        self._log("Client requested: run_transfer_100")
        success = self._two_phase_commit("T1_TRANSFER_100")
        return success

    def run_bonus_20_percent(self):
        """
        Transaction 2: Add a 20% bonus to A and the same amount to B.
        We interpret the spec as:
          bonus = 0.2 * A_original
          A := A + bonus
          B := B + bonus
        We MUST use the same 'bonus' value for both A and B, so we get
        A's current balance first, compute bonus, then run 2PC with that bonus
        as a parameter.
        """
        self._log("Client requested: run_bonus_20_percent")
        # Get A's current balance (before starting 2PC)
        try:
            a_balance = self.pA.get_balance()
        except Exception as e:
            self._log(f"Failed to read A's balance: {e}")
            return False

        bonus = int(0.2 * a_balance)
        self._log(f"A balance={a_balance}, bonus=0.2*A => {bonus}")
        params = {"bonus": bonus}
        success = self._two_phase_commit("T2_BONUS", params)
        return success

def main():
    # Ensure log file exists / clear old one
    if not os.path.exists(LOG_FILE):
        with open(LOG_FILE, "w") as f:
            f.write("")

    server = SimpleXMLRPCServer((HOST, PORT), allow_none=True, logRequests=True)
    coord = Coordinator(NODE1_URL, NODE2_URL, LOG_FILE)
    server.register_instance(coord)
    print(f"Coordinator (node0) listening on {HOST}:{PORT} ...")
    server.serve_forever()

if __name__ == "__main__":
    main()
