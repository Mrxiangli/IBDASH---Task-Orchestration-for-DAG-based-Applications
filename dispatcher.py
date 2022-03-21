import paramiko
from scp import SCPClient
import os
import json


#creat EC2 client for dispatching
def createSSHClient(server, password):
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(server,username='ec2-user', key_filename=password)
    client_traffic = SCPClient(client.get_transport())
    return client_traffic

#The dispatch function should be called when one application instance is orchestrated
def dispatch(directory, allocation,edge_list,task_dict, instance_count, dependency_dic,inputfile_dic):
	allocation_file = "allocation_"+str(instance_count)+".json"
	with open(allocation_file,'w') as allocate:
		allocate.write(json.dumps(allocation))
	for each_task in allocation.keys():
		print("task {} is allocated to edge device {}".format(each_task,allocation[each_task]))
		file_path=os.path.join(directory,task_dict[each_task])
		des_file = task_dict[each_task].split('.')[0]+"_"+str(instance_count)+".py"
		for each_device in allocation[each_task]:
			edge_list[each_device].put(file_path, des_file)
	print(inputfile_dic)
	for each in inputfile_dic:
		if inputfile_dic[str(each)][0][1]==0:
			input_path = os.path.join(directory,inputfile_dic[str(each)][0][0])
			edge_list[allocation[each][0]].put(input_path)
	# need to generated an automated python script to accomplish the task execution
	# in .json file, define the input file as x:0/1, 0 means non-intermediate files
	# Put initial input for the first stage of tasks

