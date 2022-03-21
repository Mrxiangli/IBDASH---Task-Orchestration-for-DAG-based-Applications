import argparse
import configparser
import json
import subprocess
import os

def json_file_loader(file):
	data = json.load(open(file))
	return data

def execute_main_task(main_task):
	command="python {}".format(main_task)
	return command

def task_lookup(tk, task_file):
	file = task_file[str(tk)]
	return file

def next_task(current_tk,depend_lookup,input_lookup):
	next_stage_tasks = depend_lookup[str(current_tk)]
	next_stage_dict = {}
	for each in next_stage_tasks:
		next_file=input_lookup[str(each)]
		next_stage_dict[each] = next_file
	return next_stage_dict


#Running this on each edge
if __name__ =='__main__':
	# Instantiate the parser
	parser = argparse.ArgumentParser()
	parser.add_argument('--all', type=str, nargs="?",help='allocation json file')
	parser.add_argument('--tk', type=int, help="the task that suppose to be executed in the process")
	args = parser.parse_args()

	# loading all the json files to get the status of the allocation
	allocation_dic=json_file_loader(args.all)
	dependency_dic=json_file_loader("dependency_file.json")
	task_dic=json_file_loader("task_file.json")
	depend_lookup=json_file_loader("depend_lookup.json")
	input_lookup=json_file_loader("input_lookup.json")

	#execute the main task related to this node
	task=task_lookup(args.tk, task_dic)
	command=execute_main_task(task)
	print(command)
	p=subprocess.Popen([command],shell=True,stdin=None,stdout=subprocess.PIPE,stderr=subprocess.PIPE,close_fds=True)
	out,err = p.communicate()
	if err:
		print("task {} did not finish execution, exiting!".format(task))
		os.exit()

	#looking for the dependency and find the next device and task
	next_stage_dict=next_task(args.tk,depend_lookup,input_lookup)

	#send the output from this stage to next device
	for each_tk in bext_stage_dict.keys():
		ed = allocation_dic[each_tk]
		# drop the input file to the designated device
		# start the execution 

	


	print(next_stage_dict)


	print(input_lookup)
	print(depend_lookup)
	print(task)
	# 
	print(allocation_dic)
	print(dependency_dic)
	print(task_dic)
	