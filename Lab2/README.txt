Aidan Rohm & Alex Brooke
Distributed Systems
Professor Mao

LAB 2 - README - 13 Novemeber, 2025

OVERVIEW:

This lab assignment provides a basic implementation of the Basic Paxos consistency protocol across three distributed nodes. 
Each node acts as either a proposer, acceptor, and learner while maintaining a shared file (CISC5597), which represents 
the chosen values that are proposed by the different nodes.

The general purpose of this lab is to demonstrate what happens when:
	1. A single proposer proposes a value
	2. Two proposers compete to have their proposals accepted
		a. This occurs when the first proposal wins
		b. When the second proposal overrides the first one (higher proposal number)

SYSTEM OVERVIEW:

Cluster Configuration - 

Node		Internal IP	External IP			Role						Port
Node-0		10.128.0.2	34.63.196.172		Proposer/Acceptpr/Learner	17000
Node-1		10.128.0.3	34.9.238.24			Proposer/Acceptpr/Learner	17000
Node-2		10.128.0.5	34.42.170.215		Proposer/Acceptpr/Learner	17000

The internal IPs are used here for internal communication within the cluster itself. The
external IPs are used only when trying to connect to the system from a machine outside of the
cluster itself. These Internal and External IPs would need to be changed depending on the 
setup of your own system.

Prerequisites-

	1. Python3 must be installed on each of the nodes
	2. The repository can be cloned using the following command:
		git clone https://github.com/aidanrohm/Distributed-Systems.git
	3. Navigate to this directory and be sure the following files are present:
		a. paxos-server-test.py
		b. paxos-client-test.py

Node Configuration - 

Inside of each distribution of paxos-server-test.py, assure that the following is set before
running each node
(using the IP addresses associated with your system):
	ALL_NODES = [
    		('10.128.0.2', 17000),
    		('10.128.0.3', 17000),
			('10.128.0.5', 17000)
	]
Then, update the NODE_ID that corresponds to the machine that you are configuring. In our case:
	Node		NODE_ID
	Node-0		1
	Node-1		2
	Node-2		3

RUNNING THE SIMULATION:

Step 1: Start the Paxos Servers-
	Run the following command on each node in separate SSH windows:
		python3 paxos-server-test.py
	The terminal will appear to hang, but this is simply because there is no output coming from the server code.
	All servers are now listening for RPC connections and are ready to form the Paxos cluster. There will be text
	output from the servers that reflect when they are preparing and accepting certain proposals.

Step 2: Test 1 - Single Proposer
	From any node (in a new SSH window) run the client code using the command:
		python3 paxos-client-test.py
	Expected Output:
		"SubmitValue SUCCEEDED. Chosen value = Hello from clientA
		Current value on this node: Hello from clientA"
	This is an indication that all three nodes have agreed on the same chosen value

Step 3: Test 2 - Two Competing Proposers (A wins)
	On node-0 run the command:
		python3 paxos-client-test.py
	Quickly run the same command on node-1:
		python3 paxos-client-test.py
	(remember to do this in separate windows from the server code, this way it does not interfere)
	It is expected that both proposers attempt to initiate consensus simulatneously.
	One of them (A) will win, and all nodes will agree on "Hello from clientA," including the losing proposer.

Step 4: Test 3 - Two Competing Proposers (B wins)
	Repeat the previous test but client B should be run slightly earlier. This can be done by introducing a delay in node-0's script.
	Example Adjustment to node-0's client:
		# This can be used to dictate how quickly node-0 actually executes. 
		# Simulating a delay in communication between the client and the server itself.
		import time
		time.sleep(random.uniform(0, 2))
	It is expected that the second proposer (coming from node-1) sends a higher proposal number. Because of this, the cluster should adopt
	B's value as the final chosen one, and output from each of the nodes should reflect this.

Step 5: Verifying Consensus
	On each node, run the command:
		cat CISC5597
	All files should contian the same chosen value after each test.

RESETTING BETWEEN TESTS

To clear the old state in between tests, the following can be run:
	(ctrl) + c 
	rm -f CISC5597
This will quit the server process and clear the file from the working directory, allowing us to start fresh for a new test


