import os.path
import subprocess

while not os.path.exists('predict.txt'):
	pass

time_file = open("time.txt","a")
p=subprocess.Popen(["date +%s%N"],shell=True,stdin=None,stdout=subprocess.PIPE,stderr=subprocess.PIPE,close_fds=True)
out,err = p.communicate()
time_file.write(str(out))
time_file.close()