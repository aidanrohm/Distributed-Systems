Aidan Rohm & Alex Brooke
Distributed Systems
Professor Mao

LAB 3 - README - 4 December, 2025

OVERVIEW:

This lab assignment implements the Two-Phase Commit (2PC) protocol across a distributed system. The system models
a simplified banking application consisting of three separate nodes.
    - Account A (managed by node-1)
    - Account B (managed by node-2)
    - A coordinator node (controlled by node-0) that performs the 2PC protocol
The intent of the lab is to demonstrate how a coordinator successfully ensures atomicity across different participant
nodes, guaranteeing that a transaction commits on all nodes OR aborts on all nodes.
The implementation simulates three required cases:
    1. Normal Operation
        - Transaction 1 (T1): Transfer $100 from Account A to Account B (node-1 -> node-2)
        - Transaction 2 (T2): Add a 20% bonus to both accounts
    2. Insufficient Funds Case 
        - T1 must abort because Account A does not have sufficient funds to make a $100 transfer 
        - T2 can still execute successfully
    3. Failure Scenarios (simulated with timeouts)
        - A participant crashes (times out) before voting
        - A participant crashes (times out) after voting but before the commit
These three scenarios demonstrate the reliability and safety guarantees of the atomic 2PC protocol.

SYSTEM OVERVIEW:
    
    Cluster Configuration - The following three nodes form the 2PC system:
    NODE            INTERNAL IP             EXTERNAL IP             ROLE                        PORT 
    ------------------------------------------------------------------------------------------------
    node-0          10.128.0.2              136.119.142.39          Coordinator                 8000
    node-1          10.128.0.3              35.225.33.220           Participant/Account A       8001
    node-2          10.128.0.5              136.116.2.46            Participant/Account B       8002

    The Internal IPs are used for all node-to-node RPC communication. External IPs are only used when the client runs
    outside of the cluster. THESE VALUES MUST BE CHANGED IN THE SCRIPT TO MATCH YOUR SYSTEM CONFIGURATION.

PREREQUISITES:

    1. Python 3 must be installed on each VM in the cluster. This can be done by running:
        sudo apt update
        sudo apt install -y python3 python3-pip 
    2. Clone the git repository containing the lab's code and documentation:
        git clone https://github.com/aidanrohm/Distributed-Systems.git
    3. Ensure that the following files exist in the Lab3 directory, and navigate to this directory.
        - participantA.py
        - participantB.py 
        - coordinator.py 
        - client.py 

NODE CONFIGURATION:

    Before running the system, ensure the following IP bindings are correct inside each file.
    REMINDER: They must match the configuration of your cluster in order for it to work.

    1. node-0 (Coordinator: coordinator.py)
        HOST = "10.128.0.2"
        NODE1_URL = "http://10.128.0.3:8001/"
        NODE2_URL = "http://10.128.0.5:8002/"
        PORT = 8000
    2. node-1 (Participant A: participantA.py)
        HOST = "10.128.0.3"
        PORT = 8001
    3. node-2 (Particpant B: participantB.py)
        HOST = "10.128.0.5"
        PORT = "8002"
    
    Client Configuration:

        - If running the client script on node-0:
            COORDINATOR_URL = "http://10.128.0.2:8000/"
        - If running the client script externally:
            COORDINATOR_URL = "http://136.119.142.39:8000/"

RUNNING THE SIMULATION:

    1. Start the Participant Servers:
        Open separate SSH terminals for each node, navigate to the Lab3 directory.
        The following commands should be entered in order:

        On node-1, run:
            python3 participantA.py 
        On node-2, run:
            python3 participantB.py
        
        Both of these executions will idle, this is normal as they are waiting for RPC instructions from the coordinator
    
    2. Start the Coordinator:
        SSH into node-0 in a new terminal window, navigate to the Lab3 directory.

        Run:
            python3 coordinator.py
        
        This node will now control the 2PC protocol across the participants.

    3. Run Scenario 1 (Normal Operation)
        SSH into node-0 in a new terminal window, navigate to the Lab3 directory.

        Run:
            python3 client.py

        Expected Results:
            Initial Balances:
                A = 200
                B = 300
            After T1:
                A = 100
                B = 400
            After T2:
                A = 120
                B = 420
            The client will display:
            "Final balances after Scenario 1.a: {'A': 120, 'B': 420}

    4. Run Scenario 2 (Insufficient Funds)
        Expected Results:
            Initial Balances:
                A = 90
                B = 50
            T1 must abort because A < 100 (A's balance is below the transfer amount).
            T2 computes a bonus of .2 X 90 = 18, and adds it to each account.

            The client will display:
            "Final balances after Scenario 1.b: {'A': 108, 'B': 68}
    
    5. Failure Scenario Testing
        Failure behavior is triggered by editing inside of participantB.py:
            CRASH_BEFORE_VOTE = False (change to True)
            CRASH_AFTER_VOTE = False (change to True)
        
        Case 1:
            The participant never responds -> the coordinator aborts the transaction.
            CRASH_BEFORE_VOTE = True
            The logs will show:
                Exception contacting B during prepare
                Transaction aborted.
        Case 2:
            The participant votes YES, then dies.
            CRASH_AFTER_VOTE = True
            The coordinator sends the commit, recovery would be required but the simulation will end here.

VERIFYING THE RESULTS:

    Method 1: Coordinator Query
        The output can be verified from the client output.
    
    Method 2: Inspect the participant's local state
        On node-1, run:
            cat account_A.txt
        On node-2, run:
            cat account_B.txt
    
    Method 3: Review the logs
        log_node0_coordinator.txt
        log_node1_A.txt
        log_node2_B.txt

        These show each prepare, vote, commit, and abort phase, along with any crash behavior.

RESETTING BETWEEN TESTS:

    This is only really necessary when doing the two tests, where the timeouts are activated to simulate failures.

    Stop each running server using:
        CTRL + C

    On node-1, run:
        rm -f account_A.txt
    
    On node-2, run:
        rm -f account-B.txt
    
    Restart the servers in the same order that was previously described.


