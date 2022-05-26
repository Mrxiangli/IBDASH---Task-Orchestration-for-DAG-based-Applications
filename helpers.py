import numpy as np
import sys
import pprint
import json
import networkx as nx
from matplotlib import pyplot as plt
import pandas
import numpy as np
from sklearn import linear_model
from sklearn.preprocessing import PolynomialFeatures
import os
import pandas as pd
import configparser
import json
import subprocess
import os
import sys
import socket
import time
from threading import Thread
import threading
from queue import Queue
from icmplib import ping, multiping
import global_var
import ast

pp = pprint.PrettyPrinter(indent=4)

PING_PACKET_SIZE=64
lock = threading.Lock()

# this function insert and edge device to the ED_m and ED_c matrix
def insert_edge_device(ED_m, ED_c, num_edge,new_edm_info, new_edc_info, ed_dict, ed_info):
	row_m,col_m = ED_m.shape
	row_c,col_c = ED_c.shape
	if len(new_edm_info) != col_m:
		print("the required info of the new edge device is incomplete, edge device cann't be added.")
		return ED_m, ED_c, num_edge
	if len(new_edc_info) != col_c:
		print("the required info of the new edge device is incomplete, edge device cann't be added.")
		return ED_m, ED_c, num_edge
	else:
		ED_m=np.append(ED_m,[new_edm_info],axis=0)
		ED_c=np.append(ED_c,[new_edc_info],axis=0)
		num_edge +=1
		ed_dict[num_edge-1]=ed_info; # update the new edge device avialble resource in the dictionary
		return ED_m, ED_c, num_edge, ed_dict

# this helper function extract a patch rows:row_r x col_s:col_e
def extract_blocks(row_s, row_e, col_s, col_e, block):
	row,col=block.shape
	new_array=np.empty((0,col_e-col_s+1))
	for i in range(row):
		if i>= row_s and i <= row_e:
			new_array=np.append(new_array,[block[i][col_s:col_e+1]],axis=0)
	return new_array

# this did not pass exhaustive test, need to test on the reliability of this code
def insert_task(ED_m, ED_c, num_edge, num_task, new_edm_info, new_edc_info):
	row_m,col_m = ED_m.shape
	row_c,col_c = ED_c.shape
	new_EDm=np.empty((num_edge,0))
	if new_edm_info.shape[1] != 2*num_task+1 or new_edm_info.shape[0] !=  num_edge:
		print("the required info of the new task on each device is incomplete, task can't be added edm.")
	if new_edc_info.shape[1] != 1 or new_edc_info.shape[0] !=  num_edge:
		print("the required info of the new task on each device is incomplete, task can't be added edc.")
	else:
		for i in range(num_task):
			new_EDm=np.append(new_EDm, extract_blocks(0,num_edge-1,i*num_task,i*num_task+num_task-1,ED_m), axis=1)
			new_EDm=np.append(new_EDm,extract_blocks(0,num_edge-1,i,i,new_edm_info),axis=1)
		new_EDm=np.append(new_EDm,extract_blocks(0,num_edge-1, num_task, 2*num_task, new_edm_info),axis=1)
		new_EDc=np.append(ED_c,new_edc_info,axis=1)
		num_task += 1
	return new_EDm, new_EDc, num_task


def BFS(edge_adj):
	vert_dict={}
	for u in edge_adj.keys():
		if u not in vert_dict.keys():
			vert_dict[u]={'color':'white','dis':sys.maxsize,'anc': None}
	vert_dict['0']['color']="grey"
	vert_dict['0']['dis']=0
	vert_dict['0']['anc']=None
	queue=[]
	queue.append('0')
	while queue:
		u = queue.pop(0)
		for v in edge_adj[u]:
			if v != "end":
				if vert_dict[v]['color'] == 'grey':
					vert_dict[v]['dis'] = vert_dict[u]['dis'] + 1
					vert_dict[v]['anc'] = u
				if vert_dict[v]['color'] == 'white':
					vert_dict[v]['color'] = 'grey'
					vert_dict[v]['dis'] = vert_dict[u]['dis'] + 1
					vert_dict[v]['anc'] = u
					queue.append(v)
		vert_dict[u]['color'] = 'black'
	if '1' in edge_adj['s']:
		vert_dict['1']['color']="grey"
		vert_dict['1']['dis']=0
		vert_dict['1']['anc']=None
		queue=[]
		queue.append('1')
		while queue:
			u = queue.pop(0)
			for v in edge_adj[u]:
				if v != "end":
					if vert_dict[v]['color'] == 'grey':
						vert_dict[v]['dis'] = vert_dict[u]['dis'] + 1
						vert_dict[v]['anc'] = u
					if vert_dict[v]['color'] == 'white':
						vert_dict[v]['color'] = 'grey'
						vert_dict[v]['dis'] = vert_dict[u]['dis'] + 1
						vert_dict[v]['anc'] = u
						queue.append(v)
			vert_dict[u]['color'] = 'black'
	return vert_dict	


# this returns the application in stages contain tasks in each stage
def app_stage(edge_adj):
	vert_dict = BFS(edge_adj)
	vert_dict.pop('s')
	num_vert = len(vert_dict.keys())
	stages = vert_dict[str(num_vert-1)]['dis']	# number of stages in one application instance
	stage_dict = {}
	
	for i in range(stages+1):
		if i not in stage_dict.keys():
			stage_dict[i]=[]
	for vert in vert_dict.keys():
			stage_dict[vert_dict[vert]['dis']].append(vert)
	return vert_dict, stage_dict

def task_info(vertices):
	task_dic = dict()
	for each in vertices:
		if each["name"] != "s" and each["name"] != 0:
			task_dic[each["name"]]=[each["file"],each["model"],each["depend"]]
	return task_dic

def plot(graph):
	plt.tight_layout()
	nx.draw_networkx(graph, arrows=True)
	#plt.savefig("../figures/DAG.png", format="PNG") #save plot
	plt.show() #show plot
	plt.clf()

def dag(edges):
	graph = nx.DiGraph()
	graph.add_edges_from(edges)
	graph.nodes()
	## TODO: check if the graph is cyclic
	# plot(graph)
	return graph

def linearize_dag(graph,path,paths=[]):
	datum = path[-1]              
	if datum in graph.keys():
		for val in graph[datum]:
			new_path = path + [val]
			paths = linearize_dag(graph, new_path, paths)
	else:
		paths += [path]
	return paths


def dag_linearization(f):
	# returns JSON object as a dictionary
	data = json.load(f)
	#read edges of the graph
	edge_list = []
	for source in data["Application"]["Edges"].keys():
		for target in data["Application"]["Edges"][source]:
			edge_list.append(tuple([source,target]))

	graph = dag(edge_list)
	lin_dag=linearize_dag(data["Application"]["Edges"],path=["0"],paths=[])
	#lin_list contains all the linearized chains in the DAG
	lin_list=[]
	for each_dag in lin_dag:
		tmp_dag=[]
		for idx, each in enumerate(each_dag):
			if idx < len(each_dag)-1:
				tmp_dag.append(tuple([each_dag[idx],each_dag[idx+1]]))
		lin_list.append(tmp_dag)

	#read vertices of the graph
	vertex_dict = data["Application"]["Vertices"]
	edge_adj = data["Application"]["Edges"]
	return data, graph, lin_list, vertex_dict, edge_adj

def cpu_regression_setup(task_types, num_edge, app_path):
	X_s=[]
	Y_s=[]
	X_fit=[]
	regression_models=[]
	edge_device_list=[]
	regression_task_list = []
	for i in range(task_types):
		task = "#tk"+str(i) 
		regression_task_list.append(task)
	for i in range(num_edge):
		device="ED"+str(i)+".csv"
		edge_device_list.append(device)

	for i in range(num_edge):
		tmp=pandas.read_csv(os.path.join(app_path,edge_device_list[i]))
		X_s.append(tmp[regression_task_list])
		Y_s.append(tmp['cpu_usage'])
	poly = PolynomialFeatures(degree=3)
	for i in range(num_edge):
		X_fit.append(poly.fit_transform(X_s[i]))
	for i in range(num_edge):
		regression_models.append(linear_model.LinearRegression().fit(X_fit[i],Y_s[i]))
	return regression_models

def latency_regression_setup(task_types,num_edge, EDmc_path):
	X=[100,80,50,30,10,5]
	latency_regression_model=[]
	edge_list=[]
	for i in range(num_edge):
		device="ED"+str(i)+"_latency"
		edge_list.append(device)
	for i in range(num_edge):	
		ED = np.array(pd.read_excel(EDmc_path,engine="openpyxl",sheet_name=edge_list[i],skiprows=0, nrows= task_types))
		ED_latency=[]
		for j in range(task_types):
			Y = np.log(ED[j])
			Z=np.polyfit(X, Y, 1)
			fit_func = np.poly1d(Z)
			ED_latency.append(fit_func)
		latency_regression_model.append(ED_latency)
	return latency_regression_model

# build dependency dictionary
def dependency_dic(app_data,task_dict):
	dependency_dic=dict()
	print(f"dict: {task_dict}")
	# The following code are for dependency purpose
	for main_task in app_data['Application']['Edges']:
		print(f"main_task:{main_task}")
		if main_task != 'end':
			if main_task == 's':
				for depend_task in app_data['Application']['Edges'][main_task]:
					if depend_task not in dependency_dic.keys():
						dependency_dic[int(depend_task)]=[None]
					else:
						dependency_dic[int(depend_task)].append(None)
			if main_task != 's' and main_task != 'end':
				for depend_task in app_data['Application']['Edges'][main_task]:
					if depend_task != "end":
						print(f"depend task: {depend_task}")
						if int(depend_task) not in dependency_dic.keys():
							dependency_dic[int(depend_task)]=[(main_task,task_dict[depend_task][2][main_task])]
							# the second value is used to track the type of dependency
						else:
							dependency_dic[int(depend_task)].append((main_task,task_dict[depend_task][2][main_task]))
	return dependency_dic


def update_background_tasks(task_types,backtrack_dic,ED_pred,ED_m,ED_c,ED_tasks,k,i,task,exe_only,t_pred):		
	x=[]
	for idx in range(task_types):					# go through all task types   overall time complexity V * ed * num*task_type
		x.append(ED_tasks[idx][ED_pred][k+i])		
	#print(f"x_before:{x}")
	
	# check the task on the device 
	if sum(np.array(x)>0) > 0:									# only do backtrace when there is task being affected
		for bt_task in backtrack_dic[ED_pred].keys():			# check what tasks are executing on the device
			for each_instance in backtrack_dic[ED_pred][bt_task]:		#check the instance of the tasks

				if each_instance[2] > k+i and each_instance[0] < k+i+t_pred:						# if the instance finish time is mroe than the current time, then it needs to be correct due to the new task
					w=ED_m[ED_pred][bt_task*task_types:bt_task*task_types+task_types]
					c=ED_c[ED_pred][bt_task*task_types:bt_task*task_types+task_types]
					lock=0
					if 	x[bt_task] > 0:
						x[bt_task]-=1 		#remove the task that being affected 
						lock=1
					x[task]+=1	#add the new tasks
	
					if sum(np.array(x)>0) == 0:	# if no task is on the device
						adjusted_time = c[task]
					else:
						adjusted_time = int(np.dot(w,x)+np.dot((np.array(x)>0),c)) 		# re-evaluate the time off the affected task with the new added task

					extra_time=0
					if adjusted_time > each_instance[1] - each_instance[0]: 			## adjusted time only calculated execution time, not the data transfer time, should add that as well then scale
						#multiplier = adjusted_time/(each_instance[1] - each_instance[0])
						#time_left = each_instance[2] - (k+i)
						#extra_time = int((multiplier-1)*time_left)
						extra_time=adjusted_time-(each_instance[1] - each_instance[0])
				#		print(f"extra_time: {extra_time}")
						for j in range(each_instance[2], each_instance[2]+extra_time):	
							ED_tasks[bt_task][ED_pred][j]+=1	
					if lock == 1:		
						x[bt_task]+=1 			#add itself back to keep consistent
					x[task]-=1    # remove the new one
				#	print(f"x_after:{x}")
					each_instance[1]=each_instance[0]+adjusted_time
					each_instance[2]=each_instance[2]+extra_time

	backtrack_dic[ED_pred][task].append([k+i,k+i+exe_only, k+i+t_pred])  #newly added keep tracking of the (start time, the execution only time, the end time)
	return	ED_tasks, backtrack_dic


def inputfile_dic(app_data):
	inputdict={}
	for node in app_data['Application']['Vertices']:
		if node['name']!="s":
			inputdict[node['name']]=node['input']
	return inputdict


def dependency_lookup(app_data):
	depend_lookup={}
	for each in app_data['Application']['Edges']:
		if each!="s":
			depend_lookup[each] = app_data['Application']['Edges'][each]
	return depend_lookup

def inputfile_lookup(app_data):
	input_lookup={}
	for each in app_data['Application']['Vertices']:
		if each['name']!="s":
			input_lookup[each['name']] = each['input']
	return input_lookup

def output_lookup(app_data):
	output={}
	for each in app_data['Application']['Vertices']:
		if each['name']!="s" and each['name']!='end':
			output[each['name']] = each['output']
	return output

def get_times_stamp(app_instance):
	time_file = open("time.txt","a")
	p=subprocess.Popen(["date +%s%N"],shell=True,stdin=None,stdout=subprocess.PIPE,stderr=subprocess.PIPE,close_fds=True)
	out,err = p.communicate()
	time_file.write("instance {} start:".format(app_instance))
	time_file.write(out.decode("utf-8"))
	#print("writing instance {} start".format)
	time_file.close()

def ping_test(ed):
	command = "fping -c1 -t150 {}".format(ed)
	p=subprocess.Popen([command],shell=True,stdin=None,stdout=subprocess.PIPE,stderr=subprocess.PIPE,close_fds=True)
	out,err = p.communicate()
	out = out.decode("utf-8")
	err = err.decode("utf-8")
	#loss = err.split(":")[1].split(",")[0].split("/")[-1].split("%")[0]
	#if int(loss) > 5:
	#	return -1
	#else:
	#	return 1

def socket_connections(host,port):
	s = socket.socket()
	print(f"[+] Connecting to {host}:{port}")
	s.connect((host, port))
	s.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
	print("[+] Connected.")
	return s


def send_files(s,filename):
	
	SEPARATOR = "<SEPARATOR>"
	BUFFER_SIZE = 65536 # send 4096 bytes each time step
	NAME_SIZE = 256
	
	lock.acquire()
	filesize = os.path.getsize(filename)
	name=f"{filename}{SEPARATOR}{filesize}{SEPARATOR}".ljust(NAME_SIZE).encode()
	s.send("F".encode())
	s.send(name)

	with open(filename, "rb") as f:
		bytes_read = f.read(filesize)
		s.sendall(bytes_read)
	s.send("/EOF".encode())
	lock.release()


def send_command(s,msg):
	SEPARATOR = "<SEPARATOR>"
	BUFFER_SIZE = 4096 # send 4096 bytes each time step
	MSG_SIZE = 256
	lock.acquire()
	s.send("C".encode())
	s.send(msg.ljust(MSG_SIZE).encode())
	lock.release()

def send_size_update(s,input,output,task):
	SEPARATOR = "<SEPARATOR>"
	BUFFER_SIZE = 4096 # send 4096 bytes each time step
	MSG_SIZE = 1024
	TASK_ID_SIZE = 10
	lock.acquire()
	s.send("S".encode())
	s.send(str(task).encode().ljust(TASK_ID_SIZE))
	s.send(input.ljust(MSG_SIZE))
	s.send(output.ljust(MSG_SIZE))
	lock.release()

def send_label(s,label):
	LABEL_SIZE = 256
	lock.acquire()
	s.send("L".encode())
	s.send(str(label).ljust(LABEL_SIZE).encode())
	lock.release()

def send_clean_command(instance_count):
	MSG_SIZE = 256
	for s in global_var.socket_list:
		lock.acquire()
		s.send("X".encode())
		clean_command = f"rm -r $(ls | grep '_{instance_count}.jpg\|_{instance_count}.mp4\|_{instance_count}.txt\|_{instance_count}.json\|_{instance_count}.csv')"
		s.send(clean_command.ljust(MSG_SIZE).encode())
		lock.release()

def send_ntwk_test(s):
	LABEL_SIZE = 256
	s.send("P".encode())

# interleaveing issue!
def connection_creation_thread(connection_queue):
	# device's IP address
	SERVER_HOST = "0.0.0.0"
	SERVER_PORT = 5001
	# receive 4096 bytes each time
	SEPARATOR = "<SEPARATOR>"
	# create the server socket
	# TCP socket
	s = socket.socket()
	s.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)

	# bind the socket to our local address
	s.bind((SERVER_HOST, SERVER_PORT))

	# enabling our server to accept connections
	# 5 here is the number of unaccepted connections that
	# the system will allow before refusing new connections
	s.listen(100)
	while True:
		client_socket, address = s.accept() 
		print("waiting for connection")
		connection_queue.put([client_socket,address])
		print(f"size of queue: {connection_queue.qsize()}")

def spawn_listening_thread(connection_queue):
	while True:
		#print(f"size of queue: {connection_queue.qsize()}")
		while connection_queue.qsize() != 0:
			print("waiting for connection queue to be filled")
			client_socket,address = connection_queue.get()
			Thread(target = connection_listening_thread, args=(client_socket,address)).start() #for each socket creating a listening thread

def connection_listening_thread(client_socket,address):
	global ntwk_matrix
	BUFFER_SIZE = 65536
	NAME_SIZE = 256
	LABEL_SIZE = 256
	REQUEST_SIZE=1024
	SEPARATOR = "<SEPARATOR>"
	TASK_ID_SIZE=10

	print(f"socket at {address} is being listened")

	while True:
		msg_type = client_socket.recv(1).decode()
		if msg_type != "F" and msg_type !="C" and msg_type!="" and msg_type != "L" and msg_type != "T" and msg_type != "U":

			print(f"msg: {msg_type}")
			print(f"socket {client_socket} out of sync")
			return -1
			#sys.exit()

		if msg_type == 'T':
			received_id = receive_request(NAME_SIZE,client_socket).decode()
			test_result = receive_request(NAME_SIZE,client_socket).decode()
			p2p_result=ast.literal_eval(test_result)
			for key in p2p_result.keys():
				if key == int(received_id):
					pass
				else:
					global_var.ntwk_matrix[int(received_id)][key]=p2p_result[key]
		
		if msg_type == "R":
				file_requested = receive_request(NAME_SIZE,client_socket).decode().strip()
				if os.path.exists(str(file_requested)) == True:
					send_files(client_socket,str(file_requested))
		
		if msg_type == 'U':
			tk_id = receive_request(TASK_ID_SIZE,client_socket)
			#tk_id = client_socket.recv(TASK_ID_SIZE).decode()
			input_size = ast.literal_eval(receive_request(REQUEST_SIZE,client_socket).decode().strip())
			output_size = ast.literal_eval(receive_request(REQUEST_SIZE,client_socket).decode().strip())
			print("===============================================================")
			print(f"input size: {input_size}")
			print(f"output size: {output_size}")
			#ensure the length is the same
			try:
				if len(input_size.keys())==len(global_var.in_out_history[int(tk_id)]['input'].keys()):
					input_size_list = []
					for each_key in input_size.keys():
						input_size_list.append(float(input_size[each_key]))
					for each_key in global_var.in_out_history[int(tk_id)]['input'].keys():
						if len(global_var.in_out_history[int(tk_id)]['input'][each_key]) > 20:
							for i in range(10):
								global_var.in_out_history[int(tk_id)]['input'][each_key].pop(0)
						else:
							global_var.in_out_history[int(tk_id)]['input'][each_key].append(input_size_list.pop(0))
			except:
				pass
			
			try: 
				if len(output_size.keys())==len(global_var.in_out_history[int(tk_id)]['output'].keys()):
					output_size_list = []
					for each_key in output_size.keys():
						output_size_list.append(float(output_size[each_key]))
					for each_key in global_var.in_out_history[int(tk_id)]['output'].keys():
						if len(global_var.in_out_history[int(tk_id)]['output'][each_key]) > 20:
							for i in range(10):
								global_var.in_out_history[int(tk_id)]['output'][each_key].pop(0)
						else:
							global_var.in_out_history[int(tk_id)]['output'][each_key].append(output_size_list.pop(0))
			except:
				pass

		if msg_type == 'F':
			start = time.time()
			received = client_socket.recv(NAME_SIZE).decode()
			filename, filesize, space = received.split(SEPARATOR)
			# remove absolute path if there is
			filename = os.path.basename(filename)
			instance_count = int(filename.split('_')[-1].split('.')[0])
			# convert to integer
			filesize = int(filesize)
			
			#Receiving files
			received_size = 0
			count = 0
			bytes_read = b''
			with open(filename, "wb") as f:
				counter = 0
				while (filesize - received_size) > BUFFER_SIZE:
					bytes_read_chunk = client_socket.recv(BUFFER_SIZE)
					bytes_read+=bytes_read_chunk
					received_size += len(bytes_read_chunk)
					counter+=1
				residue = filesize - received_size

				while residue > 0:
					bytes_read_chunk = client_socket.recv(residue)
					bytes_read += bytes_read_chunk
					received_size += len(bytes_read_chunk)
					if len(bytes_read) - residue == 0:
						break
					else:
						residue -= len(bytes_read_chunk)

				f.write(bytes_read)
				end = time.time()
				if received_size == filesize:
					bytes_read = client_socket.recv(4)
					if bytes_read.decode() != "/EOF":
						print(f" error transmitting {filename}")
			print(f"{filename} is received at {time.time()}")
			send_clean_command(instance_count)
			#as this take result back, which means one application instance is all done remove all the meta files
	print("socket closed ==================================")
	s.close()

def network_test():
	p2p_test={}
	for idx,ip_address in enumerate(global_var.device_list):
		result = ping(ip_address,count=5,payload_size=1024,interval=0.05,privileged=False)
		p2p_test[idx]=round(((1024/(result.avg_rtt/2))*1000)/1000000,2)
	return p2p_test
	# the last device in the deive list is orchestrator

def create_ntwk_matrix(num_edge):
	ntwk_matrix = [[0 for i in range(num_edge)] for j in range(num_edge)]
	for i in range(num_edge):
		ntwk_matrix[i][i]=-1
	return ntwk_matrix 

def ntwk_matrix_update(ntwk_dic,ntwk_matrix, identifier):
	# extract all transmisson speed from the orchestator initiated test
	total_device = len(ntwk_dic.keys())
	for j in range(0,total_device-1):
		if identifier==j:
			ntwk_matrix[identifier][j]=-1
		else:
			ntwk_matrix[identifier][j]=ntwk_dic[j]
	return ntwk_matrix

def loading_input_files(dependency_dic,depend_lookup,input_lookup,output_lookup,task_file_dic,access_dict):
	dependency_file = "dependency_file.json"
	with open(dependency_file,'w') as depend_file:
		depend_file.write(json.dumps(dependency_dic))
	depend_file.close()

	task_file = "task_file.json"
	with open(task_file,'w') as tk_file:
		tk_file.write(json.dumps(task_file_dic))
	tk_file.close()

	dependency_lookup = "depend_lookup.json"
	with open(dependency_lookup,'w') as lk_file:
		lk_file.write(json.dumps(depend_lookup))
	lk_file.close()

	input_lp = "input_lookup.json"
	with open(input_lp,'w') as lp_file:
		lp_file.write(json.dumps(input_lookup))
	lp_file.close()

	output_lp = "output_lookup.json"
	with open(output_lp,'w') as op_file:
		op_file.write(json.dumps(output_lookup))
	op_file.close()

	edge_list = "edge_list.json"
	with open(edge_list,'w') as edge_file:
		edge_file.write(json.dumps(access_dict))
	edge_file.close()
	return dependency_file,task_file,dependency_lookup,input_lp,output_lp,edge_list

def periodic_network_test():
	threading.Timer(100, periodic_network_test).start()
	ntwk_test=network_test()
	global_var.ntwk_matrix=ntwk_matrix_update(ntwk_test,global_var.ntwk_matrix, global_var.IDENTIFIER)
	for idx in range(len(global_var.socket_list)):
		send_ntwk_test(global_var.socket_list[idx])
	print(global_var.ntwk_matrix)

def creat_input_output_regression_history(app_path,dependency_dic,input_lookup,output_lookup):
	inout={}
	for task in dependency_dic.keys():
		if dependency_dic[task]== [None]:
			inout[task]={"input":{}, "output":{}}
			input_file_list = input_lookup[str(task)]
			output_file_list = output_lookup[str(task)]
			for each_inputfile in input_file_list:
				input_file = each_inputfile[0]+each_inputfile[2]
				each_filesize=os.path.getsize(os.path.join(app_path,input_file))
				if input_file not in inout[task]["input"].keys():
					inout[task]["input"][input_file]=[]	#b to Mb 
				else:
					inout[task]["input"][input_file].append([])
			for each_outputfile in output_file_list:
					output_file = each_outputfile[0]
					if output_file not in inout[task]["input"].keys():
						inout[task]["output"][output_file]=[]	
		else:
			inout[task]={"input":{}, "output":{}}
			input_file_list = input_lookup[str(task)]
			output_file_list = output_lookup[str(task)]
			for each_inputfile in input_file_list:
					input_file = each_inputfile[0]
					if input_file not in inout[task]["input"].keys():
						inout[task]["input"][input_file]=[]	
			for each_outputfile in output_file_list:
					output_file = each_outputfile[0]
					if output_file not in inout[task]["input"].keys():
						inout[task]["output"][output_file]=[]	
	return inout

def update_input_output_regression_history(socket_list,instance_count,dependency_dic,dispatcher_dic,input_lookup,output_lookup):
	instance_count=instance_count-9
	for task in dependency_dic.keys():
			input_file_list = input_lookup[str(task)]
			input_size_request_list=[]
			for each_inputfile in input_file_list:
				if each_inputfile[1] != 0:
					input_file = each_inputfile[0]+str(instance_count)+each_inputfile[2]
				else:
					input_file = each_inputfile[0]+each_inputfile[2]
				input_size_request_list.append(input_file)
			output_file_list = output_lookup[str(task)]
			output_size_request_list=[]
			for each_outputfile in output_file_list:
				output_file = each_outputfile[0]+str(instance_count)+each_outputfile[2]
				output_size_request_list.append(output_file)
			task_allocation = dispatcher_dic[instance_count][str(task)]
			#use the lowest latency allocation to ensure the update pace is fast
			send_size_update(socket_list[int(task_allocation[0])],str(input_size_request_list).encode(),str(output_size_request_list).encode(),task)
			#print(f"+=========task {task}==========+")
			#print(input_size_request_list)
			#print(output_size_request_list)

def receive_request(size,client_socket):
	bytes_read = client_socket.recv(size)
	while size - len(bytes_read) != 0:
		bytes_read += client_socket.recv(size - len(bytes_read))
	return bytes_read