# IBDASH -  Interference Based DAG Application Scheduling for Multi-Access Edge Computing

The framework of IBDASH can be divided into two parts: **Orchestrator** and **Client**. Orchestrator is where all the orchestrator started. When the orchestrator receives an application request (in DAG form), it starts orchestrating the task allocation based on the pre-profiled data of each client that joins the edge computing network, and then initiates the start of the application. On the clients' sides, each client is aware of the task allocation of the application and they perform the jobs assigned to them by the orchestrator individually and pass the intermediate results to the next task in the DAGs. The communication between clients is in a P2P manner. In the network, each node can act as an orchestrator as well as an client.

## Installation

To replicate the results shown in the paper, the steps listed below need to be followed to get the correct environment setup.

We used python 3.7.2 on both clients' and orchestrator side. To install python 3.7.2, do the following steps

First, install the required packages needed for building python
```
$sudo apt-get install build-essential checkinstall
sudo apt-get install libreadline-gplv2-dev libncursesw5-dev libssl-dev libsqlite3-dev tk-dev libgdbm-dev libc6-dev libbz2-dev libffi-dev liblzma-dev 
```
Then, download python 3.7.2 and install it.
```
sudo wget https://www.python.org/ftp/python/3.7.2/Python-3.7.2.tgz
sudo ./configure
sudo make altinstall
```
Once it is successfully installed, then install the required packages 
