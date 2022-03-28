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
client.connect("ec2-100-24-240-119.compute-1.amazonaws.com",username='ec2-user', key_filename="IBDASH_V2.pem")
client_scp = SCPClient(client.get_transport())

client_scp.put("IBDASH_V2.pem")
