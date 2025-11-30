# participantA.py
#
# Node1 = participant that manages account A.
# Exposes RPC methods to take part in 2PC:
#   - prepare(transaction_id, tx_type, params)
#   - commit(transaction_id)
#   - abort(transaction_id)
#   - get_balance()
#   - set_balance(new_value)  (for initializing scenarios)
#
# Adjust HOST / PORT for your node1 machine.

from xmlrpc.server import SimpleXMLRPCServer
import threading
import time
import os

HOST = "10.128.0.3"   # node-1 internal IP
PORT = 8001

ACCOUNT_NAME = "A"
ACCOUNT_FILE = "account_A.txt"
LOG_FILE = "log_node1_A.txt"

# Crash simulation flags for requirement 1.c
CRASH_BEFORE_VOTE = False
CRASH_AFTER_VOTE = False

class AccountParticipant:
    def __init__(self, account_name, account_file, log_file):
        self.account_name = account_name
        self.account_file = account_file
        self.log_file = log_file
        
        self.prepared_transactions = {}
        self.lock = threading.Lock()
        self._ensure_account_file()

    # ---------- Internal helpers ----------

    def _ensure_account_file(self):
        """Create the file if it doesn't exist, defaulting to 0."""
        if not os.path.exists(self.account_file):
            with open(self.account_file, "w") as f:
                f.write("0\n")

    def _log(self, msg):
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        line = f"[{timestamp}] [{self.account_name}] {msg}"
        print(line)
        with open(self.log_file, "a") as f:
            f.write(line + "\n")

    def _read_balance(self):
        with open(self.account_file, "r") as f:
            return int(f.read().strip())

    def _write_balance(self, value):
        with open(self.account_file, "w") as f:
            f.write(str(value) + "\n")

    # ---------- RPC methods ----------

    def get_balance(self):
        with self.lock:
            bal = self._read_balance()
            self._log(f"get_balance -> {bal}")
            return bal

    def set_balance(self, new_value):
        """Helper to initialize scenarios (200/300 or 90/50)."""
        with self.lock:
            self._write_balance(int(new_value))
            self._log(f"set_balance({new_value})")
        return True

    def prepare(self, transaction_id, tx_type, params):
        """
        Phase 1 of 2PC: vote YES/NO and record prepared state.
        tx_type: 'T1_TRANSFER_100' or 'T2_BONUS'
        params: dictionary, e.g. {'bonus': 40}
        Return True for YES, False for NO.
        """
        with self.lock:
            self._log(f"PREPARE received: tx_id={transaction_id}, type={tx_type}, params={params}")

            # Simulating crash before vote
            if CRASH_BEFORE_VOTE:
                self._log("Simulating crash BEFORE vote (sleeping forever)...")
                while True:
                    time.sleep(1000)

            current_balance = self._read_balance()

            if tx_type == "T1_TRANSFER_100":
                # For account A: subtract 100, but only there is enough
                if current_balance < 100:
                    self._log(f"VOTE ABORT (insufficient funds: {current_balance})")
                    return False
                new_balance = current_balance - 100

            elif tx_type == "T2_BONUS":
                # Add bonus to A (same bonus as B) – coordinator provides the bonus value
                bonus = int(params.get("bonus", 0))
                new_balance = current_balance + bonus

            else:
                self._log(f"Unknown tx_type={tx_type}, VOTE ABORT")
                return False

            # Record prepared new balance (but DO NOT write to account file yet)
            self.prepared_transactions[transaction_id] = new_balance
            self._log(f"VOTE COMMIT, prepared new_balance={new_balance} for tx_id={transaction_id}")

            # Simulating crash after vote
            if CRASH_AFTER_VOTE:
                self._log("Simulating crash AFTER vote (sleeping forever)...")
                while True:
                    time.sleep(1000)

            return True

    def commit(self, transaction_id):
        """Phase 2 COMMIT: finalize the prepared value."""
        with self.lock:
            self._log(f"COMMIT received for tx_id={transaction_id}")
            if transaction_id not in self.prepared_transactions:
                self._log(f"  No prepared state for tx_id={transaction_id}, ignoring.")
                return False

            new_balance = self.prepared_transactions.pop(transaction_id)
            self._write_balance(new_balance)
            self._log(f"  Commit applied. New balance={new_balance}")
            return True

    def abort(self, transaction_id):
        """Phase 2 ABORT: discard any prepared state."""
        with self.lock:
            self._log(f"ABORT received for tx_id={transaction_id}")
            if transaction_id in self.prepared_transactions:
                self.prepared_transactions.pop(transaction_id)
                self._log("  Prepared state discarded.")
            else:
                self._log("  No prepared state to discard.")
        return True

def main():
    server = SimpleXMLRPCServer((HOST, PORT), allow_none=True, logRequests=True)
    participant = AccountParticipant(ACCOUNT_NAME, ACCOUNT_FILE, LOG_FILE)
    server.register_instance(participant)
    print(f"Node1 (Account {ACCOUNT_NAME}) listening on {HOST}:{PORT} ...")
    server.serve_forever()

if __name__ == "__main__":
    main()
