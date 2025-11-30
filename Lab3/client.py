# client.py
#
# Simple client that sends transaction requests to the coordinator on node0.

from xmlrpc.client import ServerProxy

COORDINATOR_URL = "http://10.128.0.2:8000/"

def main():
    coord = ServerProxy(COORDINATOR_URL, allow_none=True)

    # ------- Example usage: requirement 1.a -------
    # A=200, B=300, everything works as expected
    print("=== Scenario 1.a: A=200, B=300, no failures ===")
    coord.initialize_balances(200, 300)
    print("Running T1: transfer 100 from A to B...")
    print("  success:", coord.run_transfer_100())
    print("Running T2: 20% bonus to A and same amount to B...")
    print("  success:", coord.run_bonus_20_percent())

    # ------- Example usage: requirement 1.b -------
    # A=90, B=50, everything works as expected
    print("\n=== Scenario 1.b: A=90, B=50, no failures ===")
    coord.initialize_balances(90, 50)
    print("Running T1: transfer 100 from A to B (should fail, not enough funds)...")
    print("  success:", coord.run_transfer_100())
    print("Running T2: 20% bonus to A and same amount to B...")
    print("  success:", coord.run_bonus_20_percent())

    # For 1.c.i and 1.c.ii (node2 crash before/after responding),
    #   - edit participant_B_node2.py, set CRASH_BEFORE_VOTE or CRASH_AFTER_VOTE = True,
    #   - rerun node2 server,
    #   - then re-run one of the scenarios above.

if __name__ == "__main__":
    main()
