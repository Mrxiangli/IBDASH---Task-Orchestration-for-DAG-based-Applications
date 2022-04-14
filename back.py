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
client.connect("3.234.212.152",username='ec2-user', key_filename="IBDASH_V2.pem")
client_scp = SCPClient(client.get_transport())

for i in range(1):
    start = timer.time()
    client_scp.put("/home/jonny/Documents/Research/IBDASH_V2/governer.py")
    end = timer.time()
    print("transfer time: {}".format(end-start))
