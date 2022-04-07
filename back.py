import argparse
import configparser
import json
import subprocess
import os
import sys
import paramiko
from scp import SCPClient
import time as timer

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect("128.46.32.175",username='johnny', key_filename="IBDASH_V2.pem")
client_scp = SCPClient(client.get_transport())

for i in range(10):
    start = timer.time()
    client_scp.put("/home/jonny/Documents/Research/IBDASH_V2/p2p/server.py")
    end = timer.time()
    print("transfer time: {}".format(end-start))
