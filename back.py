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
    elif password.split(".")[1] == "johnny":
        client.connect(server,username='johnny')
    else:
        client.connect(server,username='xiang')
    client_scp = SCPClient(client.get_transport())
    return client_scp, client


scp_list_1=[]
ssh_list_1=[]
scp_list_2=[]
ssh_list_2=[]

#server_list = [("54.172.191.10","IBDASH_V2.pem"),("3.234.212.152","IBDASH_V2.pem"),("3.228.0.215","IBDASH_V2.pem")]
server_list1=[("128.46.74.171",".xiang"),("128.46.74.172",".xiang"),("128.46.74.173",".xiang"),("128.46.74.95",".xiang")]
server_list2=[("128.46.32.175",".johnny")]
for each in server_list1:
    scp,ssh = createSSHClient(each[0],each[1])
    scp_list_1.append(scp)
    ssh_list_1.append(ssh)
print(ssh_list_1)
# client = paramiko.SSHClient()
# client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
# client.connect("128.46.32.175",username='johnny', key_filename="IBDASH_V2.pem")
# client_scp = SCPClient(client.get_transport())
for each in ssh_list_1:
    each.exec_command("rm ibdash/*.txt & rm ibdash/*.npy & rm ibdash/*.py & rm ibdash/*.json")

for each in scp_list_1:
    start = timer.time()
 #   each.put("/home/jonny/Documents/Research/IBDASH_V2/profile_data/profile.py","/home/johnny/ibdash/")
 #   each.put("/home/jonny/Documents/Research/IBDASH_V2/profile_data/lightgbm/pca.py","/home/johnny/ibdash/")
 #   each.put("/home/jonny/Documents/Research/IBDASH_V2/profile_data/lightgbm/train.py","/home/johnny/ibdash/")
 #   each.put("/home/jonny/Documents/Research/IBDASH_V2/profile_data/lightgbm/com_test.py","/home/johnny/ibdash/") 
 #   each.put("/home/jonny/Documents/Research/IBDASH_V2/profile_data/lightgbm/Digits_Train.txt","/home/johnny/ibdash/")
 #   each.put("/home/jonny/Documents/Research/IBDASH_V2/profile_data/lightgbm/Digits_Test.txt","/home/johnny/ibdash/")

    each.put("/home/jonny/Documents/Research/IBDASH_V2/governer.py","/home/xiang/ibdash/")
    each.put("/home/jonny/Documents/Research/IBDASH_V2/edge_list.json","/home/xiang/ibdash/")
#    each.put("/home/jonny/Documents/Research/IBDASH_V2/profile_data/lightgbm/Digits_Train.txt","/home/xiang/ibdash/")
    end = timer.time()
    print("transfer time: {}".format(end-start))

for each in server_list2:
    scp,ssh = createSSHClient(each[0],each[1])
    scp_list_2.append(scp)
    ssh_list_2.append(ssh)

# client = paramiko.SSHClient()
# client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
# client.connect("128.46.32.175",username='johnny', key_filename="IBDASH_V2.pem")
# client_scp = SCPClient(client.get_transport())
for each in ssh_list_2:
    each.exec_command("rm ibdash/*.txt & rm ibdash/*.npy & rm ibdash/*.py & rm ibdash/*.json")

for each in scp_list_2:
    start = timer.time()
 #   each.put("/home/jonny/Documents/Research/IBDASH_V2/profile_data/profile.py","/home/johnny/ibdash/")
 #   each.put("/home/jonny/Documents/Research/IBDASH_V2/profile_data/lightgbm/pca.py","/home/johnny/ibdash/")
 #   each.put("/home/jonny/Documents/Research/IBDASH_V2/profile_data/lightgbm/train.py","/home/johnny/ibdash/")
 #   each.put("/home/jonny/Documents/Research/IBDASH_V2/profile_data/lightgbm/com_test.py","/home/johnny/ibdash/") 
 #   each.put("/home/jonny/Documents/Research/IBDASH_V2/profile_data/lightgbm/Digits_Train.txt","/home/johnny/ibdash/")
 #   each.put("/home/jonny/Documents/Research/IBDASH_V2/profile_data/lightgbm/Digits_Test.txt","/home/johnny/ibdash/")

    each.put("/home/jonny/Documents/Research/IBDASH_V2/governer.py","/home/johnny/ibdash/")
    each.put("/home/jonny/Documents/Research/IBDASH_V2/edge_list.json","/home/johnny/ibdash/")
#    each.put("/home/jonny/Documents/Research/IBDASH_V2/profile_data/lightgbm/Digits_Train.txt","/home/xiang/ibdash/")
    end = timer.time()
    print("transfer time: {}".format(end-start))


