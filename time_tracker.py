import paramiko
from scp import SCPClient
import os
import json
import sys
import subprocess


time_file = open("application_time.txt","a")
p=subprocess.Popen(["date +%s%N"],shell=True,stdin=None,stdout=subprocess.PIPE,stderr=subprocess.PIPE,close_fds=True)
out,err = p.communicate()
print(out)
time_file.writelines(str(out))
time_file.close()