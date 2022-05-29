import os.path
import subprocess
import argparse
import configparser
import time
import subprocess

if __name__ =='__main__':
	# parser = argparse.ArgumentParser()
	# parser.add_argument('--c', type=int, nargs="?")
	# parser.add_argument('--f', type=str, nargs="?")
	# parser.add_argument('--app', type=str, nargs="?")
	# args = parser.parse_args()

	# instance_count = args.c

	for counter in range(1):

		p=subprocess.Popen(["source ~/.bashrc"], shell=True,stdin=None, stdout=subprocess.PIPE,stderr=subprocess.PIPE,close_fds=True)
		out,err = p.communicate()
		time.sleep(5)
		print("source bashrc")

		# p=subprocess.Popen(["python start_test.py"], shell=True,stdin=None, stdout=subprocess.PIPE,stderr=subprocess.PIPE,close_fds=True)
		# out,err = p.communicate()
		# time.sleep(20)
		# print("starting test")


		p=subprocess.Popen(["python ibdash.py --app mapreduce --mc ED_mc_map.xlsx --sch lavea"], shell=True,stdin=None, stdout=subprocess.PIPE,stderr=subprocess.PIPE,close_fds=True)
		print("starting orchestrator")
		# out,err = p.communicate()
		# print(err)
		# print(out)
		p=subprocess.Popen(["python e2e.py --app mapreduce --c 100 --f time.txt"], shell=True,stdin=None, stdout=subprocess.PIPE,stderr=subprocess.PIPE,close_fds=True)
		out,err = p.communicate()
		time.sleep(5)
		print("starting timer")

		p=subprocess.Popen(["python end_test.py"], shell=True,stdin=None, stdout=subprocess.PIPE,stderr=subprocess.PIPE,close_fds=True)
		out,err = p.communicate()
		time.sleep(30)
		print("kill all process on edge")

		p=subprocess.Popen(["kill $(ps -ef | grep 'ibdash.py' |grep -v 'grep' | aks {'print $2'})"], shell=True,stdin=None, stdout=subprocess.PIPE,stderr=subprocess.PIPE,close_fds=True)
		out,err = p.communicate()
		time.sleep(5)
		print("kill orchestrator process")

		p=subprocess.Popen(["python time_anlysis.py --c 100 --f time.txt"], shell=True,stdin=None, stdout=subprocess.PIPE,stderr=subprocess.PIPE,close_fds=True)
		out,err = p.communicate()
		print(out)
		print("========================================================")
		time.sleep(5)

		p=subprocess.Popen(["python back.py"], shell=True,stdin=None, stdout=subprocess.PIPE,stderr=subprocess.PIPE,close_fds=True)
		out,err = p.communicate()
		time.sleep(5)
		print("cleaning and resending starting files")

		p=subprocess.Popen(["rm *.txt & rm allocation_* "], shell=True,stdin=None, stdout=subprocess.PIPE,stderr=subprocess.PIPE,close_fds=True)
		out,err = p.communicate()
		time.sleep(5)
		print("clean local temporary files")