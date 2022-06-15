

import os.path
import subprocess
import argparse
import configparser
import time
import subprocess
import signal

def handler(signum, frame):
	global lock
	res = input("Ctrl-c was pressed. Do you really want to exit? y/n ")
	if res == 'y':
		lock = False
        

if __name__ =='__main__':
	parser = argparse.ArgumentParser()
	parser.add_argument('--c', type=int, nargs="?")
	parser.add_argument('--f', type=str, nargs="?")
	parser.add_argument('--app', type=str, nargs="?")
	args = parser.parse_args()
	signal.signal(signal.SIGINT, handler)
	instance_count = args.c
	
	result_list = []
	for i in range(1, instance_count+1):
		if args.app == "lightgbm":
			file = "predict_{}.txt".format(i)
		if args.app == "video":
			file = "analytic_result_{}.txt".format(i)
		if args.app == "mapreduce":
			file = "mapreduce_result_{}.txt".format(i)
		if args.app == "matrix":
			file = "tk4_output_{}.npy".format(i)	
		result_list.append(file) 
	global lock
	lock = True
	current_dir = os.getcwd()
	timefile=os.path.join(current_dir,args.f)

	time_list = []

	prev_length=instance_count
	timer_start = time.time()
	result_received = 0
	while result_list != []:
		new_length = len(result_list)
		new_timer=time.time()
		if new_length != prev_length:
			prev_length = new_length
			timer_start = new_timer

		for each in result_list:
			if os.path.exists(each):
				result_received+=1
				print(f"received {result_received}/{instance_count}.")
				p=subprocess.Popen(["date +%s%N"],shell=True,stdin=None,stdout=subprocess.PIPE,stderr=subprocess.PIPE,close_fds=True)
				out,err = p.communicate()
				result_list.remove(each)
				instance = each.split('_')[-1].split('.')[0]
				time_list.append([instance,out.decode("utf-8")])
		if new_timer - timer_start > 700 or lock == False:
			break
				
	time_file = open(timefile,"a")

	for each in time_list:
		instance,out = each
		time_file.write("instance {} end:".format(instance))
		time_file.write(out)
	time_file.close()
