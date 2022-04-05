import argparse
import configparser
import json
import subprocess
import os
import sys
import paramiko
from scp import SCPClient
import errno

def json_file_loader(file):
	data = json.load(open(file))
	return data

def execute_main_task(main_task,instance_count):
	command="python {} --count {}".format(main_task,instance_count)
	return command

def task_lookup(tk, task_file):
	file = task_file[str(tk)]
	return file

def next_task(current_tk,depend_lookup,input_lookup):
	next_stage_tasks = depend_lookup[str(current_tk)]
	next_stage_dict = {}
	for each in next_stage_tasks:
		if each != 'end':
			next_file=input_lookup[str(each)]
			next_stage_dict[each] = next_file
	return next_stage_dict

#creat EC2 client for dispatching
def createSSHClient(server, password):
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    if password.split(".")[1] == "pem":
    	client.connect(server,username='ec2-user', key_filename=password)
    else:
    	client.connect(server,username='jonny', key_filename=password)
    client_scp = SCPClient(client.get_transport())
    return client_scp, client

def create_edge_server():
	edge_list_scp=[]
	edge_list_ssh=[]
	access_dict={}
	access_dict[0]="ec2-107-23-36-58.compute-1.amazonaws.com"
	access_dict[1]="ec2-3-239-208-120.compute-1.amazonaws.com"
	access_dict[2]="ec2-3-234-212-152.compute-1.amazonaws.com"
	access_dict[3]="128.46.73.218"
	for i in range(4):
		if i < 3:
			client_scp, client_ssh = createSSHClient(access_dict[i],"IBDASH_V2.pem")
		else:
			client_scp, client_ssh = createSSHClient(access_dict[i], password="id_rsa.pub")
		edge_list_scp.append(client_scp)
		edge_list_ssh.append(client_ssh)

	return edge_list_scp,edge_list_ssh


#Running this on each edge
if __name__ =='__main__':
	# Instantiate the parser
	parser = argparse.ArgumentParser()
	parser.add_argument('--all', type=str, nargs="?",help='allocation json file')
	parser.add_argument('--tk', type=int, help="the task that suppose to be executed in the process")
	parser.add_argument('--ic',type=int,help="instance count")
	args = parser.parse_args()

	#creating ssh connection
	edge_list_scp, edge_list_ssh = create_edge_server()

	#need to source the bashrc file to activate the corresponding conda enviroment
	#stdin,stdout,stderr=edge_list_ssh[ed].exec_command("source ~/.bashrc")

	# loading all the json files to get the status of the allocation
	instance_count=args.all.split('.')[0].split('_')[1]
	allocation_dic=json_file_loader(args.all)
	dependency_dic=json_file_loader("dependency_file.json")
	task_dic=json_file_loader("task_file.json")
	depend_lookup=json_file_loader("depend_lookup.json")
	input_lookup=json_file_loader("input_lookup.json")
	output_lookup=json_file_loader("output_lookup.json")

	#running a check to see if all input files are available; if missing, try to retrieve from replicated service
	for input_file in input_lookup[str(args.tk)]:
		if input_file[1] == 0:	#non-intermediate files
			if os.path.exists(input_file[0]):
				pass
			else:																				#missing file
				raise FileNotFoundError(errno.ENOENT, os.strerror(errno.ENOENT), input_file[0])
		else:				#intermediate files
			file_to_be_retrieved = input_file[0] + str(instance_count) + input_file[2]
			if os.path.exists(file_to_be_retrieved):
				pass
			else:		#this intermediate file is missing, go back to previous stage and fetch
				for each_depend_task in dependency_dic[str(args.tk)]:							#find all dependency of current task
					for each_device in allocation_dic[str(each_depend_task[0])]:				# find the devices that execute those dependent taks
						file_suppose_to_produced = output_lookup[each_depend_task[0]]			# find the output files suppose to be produced by those dependent tasks
						for each_file_produced in file_suppose_to_produced:						# check if the missing file is one of them
							if each_file_produced[0] == input_file[0]:
								try:
									err=edge_list_scp[int(each_device[0])].get(file_to_be_retrieved)
									if not err:
										break
								except:
									pass	

	#execute the main task related to this node
	task=task_lookup(args.tk, task_dic)
	command=execute_main_task(task, instance_count)
	#print(command)
	p=subprocess.Popen([command],shell=True,stdin=None,stdout=subprocess.PIPE,stderr=subprocess.PIPE,close_fds=True)
	out,err = p.communicate()
	#print(err)
	if err:
		#print("task {} did not finish execution, exiting!".format(task))
		sys.exit()

	output_from_current_tk = output_lookup[str(args.tk)]
	for each in output_from_current_tk:
		intermediate_file = each[0]+str(instance_count)+each[2]
		#print(intermediate_file)
		#print(each)
		for each_edge in allocation_dic[str(each[3])]:
			edge_list_scp[each_edge].put(intermediate_file)

	#looking for the dependency and find the next device and task
	next_stage_dict=next_task(args.tk,depend_lookup,input_lookup)
	#print(next_stage_dict)
	#Curent task is the last task
	if len(next_stage_dict) == 0:
		#print(input_lookup['end'])
		result_file = "predict_"+str(args.ic)+".txt"
		edge_list_scp[3].put(result_file,"/home/jonny/Documents/Research/IBDASH_V2/result")
	#send the output from this stage to next device

	for each_tk in next_stage_dict.keys():
		ed = allocation_dic[each_tk][0]
		
		#print(each_tk)
		#print(next_stage_dict[each_tk])
		# drop the input file to the designated device
		#for each_input in next_stage_dict[each_tk]:
			#print(each_input)
		#	if each_input[1] == 1: #checking the second position first to see if it is a intermediate generated file
		#		infile = each_input[0]+str(instance_count)+each_input[2]
		#		if os.path.exists(infile):
					#edge_list_scp[ed].put(infile) this is an unnecessary command; removed for now
					#print("moving {} to ed : {}".format(infile,ed))
		
		allocation_file = "allocation_"+str(args.ic)+".json"
		command = "nohup python governer.py --all {} --tk {} --ic {}".format(allocation_file,each_tk,args.ic)
		
		#print(command)
		#print("the above command execute on ed: {}".format(ed))
		#stdin,stdout,stderr=edge_list_ssh[ed].exec_command(command)
		
		edge_list_ssh[ed].exec_command(command)
		for line in stdout.read().splitlines():
			print(line)
 
	
	