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
import tqdm
import pdb
import time
from threading import Thread
import threading
from queue import Queue

pp = pprint.PrettyPrinter(indent=4)

PING_PACKET_SIZE=64


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
	# The following code are for dependency purpose
	for main_task in app_data['Application']['Edges']:
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
						if depend_task not in dependency_dic.keys():
							dependency_dic[int(depend_task)]=[(main_task,task_dict[depend_task][2][main_task])]
							# the second value is used to track the type of dependency
						else:
							dependency_dic[int(depend_task)].append((main_task,task_dict[depend_task][2][main_task]))
	return dependency_dic

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
	oput_lookup={}
	for each in app_data['Application']['Vertices']:
		if each['name']!="s" and each['name']!='end':
			oput_lookup[each['name']] = each['output']
	return oput_lookup

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

	filesize = os.path.getsize(filename)
	#print(filename)
	name=f"{filename}{SEPARATOR}{filesize}{SEPARATOR}".ljust(NAME_SIZE).encode()
	#print(name))
	print(filename)
	s.send("F".encode())
	s.send(name)
	#return

	#progress = tqdm.tqdm(range(filesize), f"Sending {filename}", unit="B", unit_scale=True, unit_divisor=1024)
	counter = 0
	with open(filename, "rb") as f:
		bytes_read = f.read(filesize)
		#print(bytes_read)
		# s.sendall(bytes_read[: :BUFFER_SIZE])

		start = time.time()
		s.sendall(bytes_read)
		# for i in range(int((filesize/BUFFER_SIZE)+1)):
		# #for i in range(200):
		# 	# read the bytes from the file
		# 	# print(sys.getsizeof(bytes_read[i*BUFFER_SIZE : (i+1)* BUFFER_SIZE: BUFFER_SIZE]))
		# 	# print(sys.getsizeof(bytes_read[:: BUFFER_SIZE]))
		# 	# temp_byte = bytes_read[i*BUFFER_SIZE : (i+1)* BUFFER_SIZE]
		# 	#pdb.set_trace()
		# 	if not bytes_read:
		# 		pdb.set_trace()
		# 		# file transmitting is done
		# 	 #   break
		# 	# we use sendall to assure transimission in 
		# 	# busy networks
		# 	# s.sendall(bytes_read[i*BUFFER_SIZE : (i+1)* BUFFER_SIZE])
		# 	s.sendall(bytes_read[: :BUFFER_SIZE])
		# 	#print("lol")
		# 	# update the progress bar
		# 	#progress.update(len(bytes_read))

		# 	# counter+=1;
		# 	print(i)
		end = time.time()
		print(f"{filename}:finishing done: {end-start}")
	s.send("/EOF".encode())
	# close the socket
	#s.close()
	#print("closed socket")


def send_command(s,msg):
	SEPARATOR = "<SEPARATOR>"
	BUFFER_SIZE = 4096 # send 4096 bytes each time step
	MSG_SIZE = 256
	s.send("C".encode())
	#return
	s.send(msg.ljust(MSG_SIZE).encode())


def send_label(s,label):
	LABEL_SIZE = 256
	print(label)
	s.send("L".encode())
	#return
	s.send(str(label).ljust(LABEL_SIZE).encode())

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
	print("sssss")
	while True:
		#print(f"size of queue: {connection_queue.qsize()}")
		while connection_queue.qsize() != 0:
			print("waiting for connection queue to be filled")
			client_socket,address = connection_queue.get()
			Thread(target = connection_listening_thread, args=(client_socket,address)).start() #for each socket creating a listening thread

def connection_listening_thread(client_socket,address):
	global IDENTIFIER
	BUFFER_SIZE = 65536
	NAME_SIZE = 256
	LABEL_SIZE = 256
	SEPARATOR = "<SEPARATOR>"

	print(f"socket at {address} is being listened")

	while True:
		msg_type = client_socket.recv(1).decode()
		if msg_type != "F" and msg_type !="C" and msg_type!="" and msg_type != "L":
			print(f"msg: {len(msg_type)}")
			print(f"msg: {msg_type}")
			print(f"socket {client_socket} out of sync")
		if msg_type == 'F':
			start = time.time()
			received = client_socket.recv(NAME_SIZE).decode()
			print(received)
			filename, filesize, space = received.split(SEPARATOR)
			# remove absolute path if there is
			filename = os.path.basename(filename)
			# convert to integer
			filesize = int(filesize)
			
			#Receiving files
			received_size = 0
			count = 0
			bytes_read = b''
			with open(filename, "wb") as f:
				#bytes_read = client_socket.recv(filesize)
				#print(len(bytes_read.decode()))
				#print(len(bytes_read))
				counter = 0
				while (filesize - received_size) > BUFFER_SIZE:
					bytes_read_chunk = client_socket.recv(BUFFER_SIZE)
					bytes_read+=bytes_read_chunk
					received_size += len(bytes_read_chunk.decode())
					counter+=1
				residue = filesize - received_size

				while residue > 0:
					bytes_read_chunk = client_socket.recv(residue)
					bytes_read += bytes_read_chunk
					received_size += len(bytes_read_chunk.decode())
					if len(bytes_read.decode()) - residue == 0:
						break
					else:
						residue -= len(bytes_read_chunk.decode())

				f.write(bytes_read)
				end = time.time()
				print(f"time: {end-start}")
				if received_size == filesize:
					bytes_read = client_socket.recv(4)
					if bytes_read.decode() != "/EOF":
						print(f" error transmitting {filename}")

	s.close()