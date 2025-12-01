# participantB.py
#
# Node2 = participant that manages account B.
# Similar RPC API as node1.

from xmlrpc.server import SimpleXMLRPCServer
import threading
import time
import os

HOST = "10.128.0.5"   # Node2 internal IP
PORT = 8002           # Port for node2's RPC server

ACCOUNT_NAME = "B"                # Name used in the logs
ACCOUNT_FILE = "account_B.txt"    # Current balance stored as an int in this file
LOG_FILE = "log_node2_B.txt"      # Logs go to this file

# Crash simulation for requirement 1.c
CRASH_BEFORE_VOTE = False         # To simulate a crash before the participant gets a chance to vote
CRASH_AFTER_VOTE = False          # To simulate a crash after the participant votes yes, but before it can commit

class AccountParticipant:
    def __init__(self, account_name, account_file, log_file):
        self.account_name = account_name
        self.account_file = account_file
        self.log_file = log_file
        self.prepared_transactions = {}
        self.lock = threading.Lock()    # Only one thread at a time can read/write balances
        self._ensure_account_file()     # Create account file if it doesn't exist 

    # ---------- Internal helpers ----------
    
    def _ensure_account_file(self):
        """Create the file if it doesn't exist, defaulting to 0."""
        if not os.path.exists(self.account_file):
            with open(self.account_file, "w") as f:
                f.write("0\n")

    # Logs a timestamped message prefixed with [B]
    # Prints to the console and appends to the log_node2_B.txt file
    def _log(self, msg):
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        line = f"[{timestamp}] [{self.account_name}] {msg}"
        print(line)
        with open(self.log_file, "a") as f:
            f.write(line + "\n")

    def _read_balance(self):
        """Reads the current balance from the account file."""
        with open(self.account_file, "r") as f:
            return int(f.read().strip())

    def _write_balance(self, value):
        """Overwrites the file with the new balance from the commits."""
        with open(self.account_file, "w") as f:
            f.write(str(value) + "\n")

    # ---------- RPC methods ----------

    def get_balance(self):
        """Thread safe read of the account balance."""
        with self.lock:
            bal = self._read_balance()
            self._log(f"get_balance -> {bal}")
            return bal

    def set_balance(self, new_value):
        """
        Helper to initialize scenarios (200/300 or 90/50).
        Based on the assignment description.
        """
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
        Called by the Coordinator
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
                # For account B: add 100
                new_balance = current_balance + 100

            elif tx_type == "T2_BONUS":
                # Add bonus to B as well
                bonus = int(params.get("bonus", 0))
                new_balance = current_balance + bonus

            else:
                self._log(f"Unknown tx_type={tx_type}, VOTE ABORT")
                return False

            # Save the tentative new balance mapped to the transaction_id
            # Do not write to the disk yet (only happens on commit)
            self.prepared_transactions[transaction_id] = new_balance
            self._log(f"VOTE COMMIT, prepared new_balance={new_balance} for tx_id={transaction_id}")

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
    # Sets up XML-RPC server on HOST and PORT
    server = SimpleXMLRPCServer((HOST, PORT), allow_none=True, logRequests=True)
    participant = AccountParticipant(ACCOUNT_NAME, ACCOUNT_FILE, LOG_FILE)
    server.register_instance(participant)    # Creates the account participant and registers its instance
    
    print(f"Node2 (Account {ACCOUNT_NAME}) listening on {HOST}:{PORT} ...")
    server.serve_forever()

if __name__ == "__main__":
    main()
