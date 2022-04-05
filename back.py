import argparse
import configparser
import json
import subprocess
import os
import sys
import paramiko
from scp import SCPClient

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect("128.46.73.204",username='jonny', key_filename="IBDASH_V2.pem")
client_scp = SCPClient(client.get_transport())

client_scp.put("/home/jonny/Documents/Research/IBDASH_V2/profile_data/lightgbm/vectors_pca.txt","/Users/jonny")
