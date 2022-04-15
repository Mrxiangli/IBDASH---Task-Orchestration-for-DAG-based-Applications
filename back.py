import argparse
import configparser
import json
import subprocess
import os
import sys
import paramiko
from scp import SCPClient
import time as timer


def createSSHClient(server, password):
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    if password.split(".")[1] == "pem":
        client.connect(server,username='ec2-user', key_filename=password)
    else:
        client.connect(server,username='johnny')
    client_scp = SCPClient(client.get_transport())
    return client_scp


scp_list=[]

server_list = [("54.172.191.10","IBDASH_V2.pem"),("3.234.212.152","IBDASH_V2.pem"),("3.228.0.215","IBDASH_V2.pem"),("128.46.32.175","pass.pd")]
for each in server_list:
    scp_list.append(createSSHClient(each[0],each[1]))

# client = paramiko.SSHClient()
# client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
# client.connect("128.46.32.175",username='johnny', key_filename="IBDASH_V2.pem")
# client_scp = SCPClient(client.get_transport())

for each in scp_list:
    start = timer.time()
    each.put("/home/jonny/Documents/Research/IBDASH_V2/governer.py")
    each.put("/home/jonny/Documents/Research/IBDASH_V2/edge_list.json")
    end = timer.time()
    print("transfer time: {}".format(end-start))
