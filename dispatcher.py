import paramiko
from scp import SCPClient
import os
import json
import sys
from helpers import *
import pdb


#The dispatch function should be called when one application instance is orchestrated
def dispatch(directory, allocation,task_dict, instance_count, dependency_dic,inputfile_dic, socket_list, non_meta_files):

	allocation_file = "allocation_"+str(instance_count)+".json"
	with open(allocation_file,'w') as allocate:
		allocate.write(json.dumps(allocation))
	allocate.close()
	tmp_ed=[]
	for each_task in allocation.keys():
		file_path=os.path.join(directory,task_dict[each_task])	
		# there is redundunt allocation file being send here
		for ed in allocation[each_task]:
			if ed not in tmp_ed:
				send_files(socket_list[ed],allocation_file)
				tmp_ed.append(ed)
			else:
				pass

			if ed not in non_meta_files.keys():
				non_meta_files[ed]=[task_dict[each_task]]
				send_files(socket_list[ed],file_path)

			else:
				if task_dict[each_task] in non_meta_files[ed]:
					pass
				else:
					non_meta_files[ed].append(task_dict[each_task])
					send_files(socket_list[ed],file_path)

	for each in inputfile_dic.keys():
		for each_file in inputfile_dic[str(each)]:
			# if the input file is not a meta file
			if each_file[1]==0:
				input_path = os.path.join(directory,each_file[0]+each_file[2])
				for each_edge in allocation[str(each)]:
					# if the device never receive any non-meta files, send the non-meta file
					if each_edge not in non_meta_files.keys():
						non_meta_files[each_edge]=[each_file[0]+each_file[2]]
						send_files(socket_list[each_edge],input_path)
					else:
						# if the non-meta file is already available, no need to send
						if (each_file[0]+each_file[2]) in non_meta_files[each_edge]:
							pass
						else:
							# the specifc non-meta file is not available on the edge
							non_meta_files[each_edge].append(each_file[0]+each_file[2])
							send_files(socket_list[each_edge],input_path)

	for eachtask in dependency_dic.keys():
		if dependency_dic[eachtask]==[None]:
			allocation_file = "allocation_"+str(instance_count)+".json"
			num_depend = len(dependency_dic[int(eachtask)])
			command = "{} {} {} {}".format(allocation_file,eachtask,instance_count,num_depend)		#num_depend is used as one more layer of guarante to ensure the task with multiple input are executed at the right time
			command = str((int(instance_count),command))		# priority command queue
			for each_edge in allocation[str(eachtask)]:
				send_command(socket_list[each_edge],command)

