import paramiko
from scp import SCPClient
import os
import json
import sys
from helpers import send_files


#creat EC2 client for dispatching
def createSSHClient(server, password):
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    if password.split('.')[1]=="pem":
    	client.connect(server,username='ec2-user', key_filename=password)
    else:
    	client.connect(server,username='jonny', key_filename=password)
    client_scp = SCPClient(client.get_transport())
    return client_scp, client

#The dispatch function should be called when one application instance is orchestrated
def dispatch(directory, allocation,task_dict, instance_count, dependency_dic,inputfile_dic, access_dict):
	allocation_file = os.path.join(directory,"allocation_"+str(instance_count)+".json")
	with open(allocation_file,'w') as allocate:
		allocate.write(json.dumps(allocation))
	allocate.close()
	for each_task in allocation.keys():
		print("task {} is allocated to edge device {}".format(each_task,allocation[each_task]))
		file_path=os.path.join(directory,task_dict[each_task])
		#des_file = task_dict[each_task].split('.')[0]+"_"+str(instance_count)+".py"
		#llocation_file_path = os.path
		for each_device in allocation[each_task]:
			send_files(access_dict[each_device],5001,file_path)
			send_files(access_dict[each_device],5001,allocation_file)
			#edge_list_scp[each_device].put(file_path)
			#edge_list_scp[each_device].put(allocation_file)

	for each in inputfile_dic:
		for each_file in inputfile_dic[str(each)]:
			if each_file[1]==0:
				input_path = os.path.join(directory,each_file[0])
				for each_edge in allocation[str(each)]:
					send_file(access_dict[each_edge],5001,input_path)
					#edge_list_scp[each_edge].put(input_path)
				#### need to figure out why vectors not passed

	for eachtask in dependency_dic.keys():
		if dependency_dic[eachtask]==[None]:
			allocation_file = "allocation_"+str(instance_count)+".json"
			command = "nohup python governer.py --all {} --tk {} --ic {}".format(allocation_file,eachtask,instance_count)
			print(command)
			#stdin,stdout,stderr=edge_list_ssh[allocation[str(eachtask)][0]].exec_command(command)
			for each_edge in allocation[str(eachtask)]:
				stdin,stdout,stderr=edge_list_ssh[each_edge].exec_command(command)
				#edge_list_ssh[each_edge].exec_command(command)
				print("edge device {} executing command {}".format(each_edge,command))
				for line in stderr.read().splitlines():
					print(line)

	#print(dependency_dic)
	#print(allocation)
	# need to generated an automated python script to accomplish the task execution
	# in .json file, define the input file as x:0/1, 0 means non-intermediate files
	# Put initial input for the first stage of tasks

