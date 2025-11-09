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

Node		Internal IP	External IP		Role				Port
Node-0		10.128.0.2	34.63.196.172		Proposer/Acceptpr/Learner	17000
Node-1		10.128.0.3	34.9.238.24		Proposer/Acceptpr/Learner	17000
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
