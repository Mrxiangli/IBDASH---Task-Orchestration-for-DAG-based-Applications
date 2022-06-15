import json
import subprocess
import sys
import errno
import socket
import os
import time
import threading
import ast

from icmplib import ping
from multiprocessing import Process
from threading import Thread
from queue import PriorityQueue, Queue

IDENTIFIER = -1
device_list = []

lock = threading.Lock()

def send_identifier(s,id):

	ID_SIZE=10
	global lock
	lock.acquire()
	s.send("Q".encode())
	s.send(str(id).ljust(ID_SIZE).encode())
	lock.release()

def json_file_loader(file):
	print(file)
	data = json.load(open(file))
	return data

def execute_main_task(main_task,instance_count):
	while os.path.exists(main_task) ==  False:
		pass
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

# Network test function: send a ping to all devices in the device list and retrieve their 
# communication speed and send the updat eback to orchestrator
def network_speed_test(device_list,transerr):
	p2p_test=network_test(device_list,transerr)
	send_ntwk_test(socket_list[-1],p2p_test,IDENTIFIER)

def network_test(device_list,transerr):
	p2p_test={}
	for idx,ip_address in enumerate(device_list):
		result = ping(ip_address,count=5,payload_size=1024,interval=0.05,privileged=False)
		#print(f"avg_rtt:{result.avg_rtt}")
		p2p_test[idx]=round(((1024/((result.avg_rtt*transerr)/2))*1000)/1000000,4)
	return p2p_test

def send_ntwk_test(s,p2p_test,identifier):
	BUFFER_SIZE = 4096 # send 4096 bytes each time step
	MSG_SIZE = 256
	global locks
	lock.acquire()
	s.send("T".encode())
	s.send(str(identifier).ljust(MSG_SIZE).encode())
	s.send(str(p2p_test).ljust(MSG_SIZE).encode())
	lock.release()

# Get the request input output pair size and send the result back 
# to the orchestrator
def update_size_proc(tk_id, input_request,output_request,client_socket):
	input_request = ast.literal_eval(input_request.decode().strip())
	output_request = ast.literal_eval(output_request.decode().strip())
	input_size_list={}
	output_size_list={}
	for each in input_request:
		if os.path.exists(each) == True:
			input_size_list[each]=round(os.path.getsize(each)/1048576,2)
	for each in output_request:
		if os.path.exists(each) == True:
			output_size_list[each]=round(os.path.getsize(each)/1048576,2)
	send_size_update(client_socket,str(input_size_list).encode(),str(output_size_list).encode(),tk_id)

def send_size_update(s,input,output,task):
	MSG_SIZE = 1024
	TASK_ID_SIZE=10
	global lock
	lock.acquire()
	s.send("U".encode())
	s.send(str(task).encode().ljust(TASK_ID_SIZE))
	s.send(input.ljust(MSG_SIZE))
	s.send(output.ljust(MSG_SIZE))
	lock.release()

# Utility function for sending files
def send_files(s,filename):
	global lock
	SEPARATOR = "<SEPARATOR>"
	NAME_SIZE = 256
	filesize = os.path.getsize(filename)
	print(f"{filename} is send at {time.time()}")
	name=f"{filename}{SEPARATOR}{filesize}{SEPARATOR}".ljust(NAME_SIZE).encode()
	lock.acquire()
	s.send("F".encode())
	s.send(name)
	with open(filename, "rb") as f:
		bytes_read = f.read(filesize)
		s.sendall(bytes_read)
	s.send("/EOF".encode())
	lock.release()

# Utility function for receving files
def receive_request(size,client_socket):
	bytes_read = client_socket.recv(size)
	while size - len(bytes_read) != 0:
		bytes_read += client_socket.recv(size - len(bytes_read))
	return bytes_read

def receive_files(filesize,BUFFER_SIZE,filename,client_socket):
	bytes_read = receive_request(filesize,client_socket)
	with open(filename, "wb") as f:
		f.write(bytes_read)

	print(f"{filename} is received")
	if len(bytes_read) == filesize:
		bytes_read = receive_request(4,client_socket)
		if bytes_read.decode() != "/EOF":
			print(f" error transmitting {filename}, exiting")
			client_socket.close()
			return -1

# Utility functon for sending command
def send_command(s,msg):
	MSG_SIZE = 256
	print(msg)
	global lock
	lock.acquire()
	s.send("C".encode())
	s.send(msg.ljust(MSG_SIZE).encode())
	lock.release()

# Utlity function for re-requesting a file that in not on the device
def send_resend_request(s,identifier,file):
	print(f"retrieving {file}")
	MSG_SIZE = 256
	global lock
	lock.acquire()
	s.send("R".encode())
	s.send(str(file).ljust(MSG_SIZE).encode())
	lock.release()

# Utility function that set up the p2p connection
def socket_connections(host,port):
	s = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
	print(f"[+] Connecting to {host}:{port}")
	s.connect((host, port))
	s.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
	s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
	print("[+] Connected.")
	return s

def connection_creation_thread(connection_queue, socket_q):
	# device's IP address
	SERVER_HOST = "0.0.0.0"
	SERVER_PORT = 5001
	# receive 4096 bytes each time
	SEPARATOR = "<SEPARATOR>"
	# create the server socket
	# TCP socket
	s = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
	s.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
	s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
	print("binding now")
	# bind the socket to our local address
	s.bind((SERVER_HOST, SERVER_PORT))
	print("finish binding")
	# enabling our server to accept connections
	# 5 here is the number of unaccepted connections that
	# the system will allow before refusing new connections
	s.listen(100)
	while True:
		client_socket, address = s.accept() 
		print("waiting for connection")
		connection_queue.put([client_socket,address])
		socket_q.put([client_socket,address])

def spawn_listening_thread(connection_queue, command_queue,label_q):
	while True:
		while connection_queue.qsize() != 0:
			print("waiting for connection queue to be filled")
			client_socket,address = connection_queue.get()
			Thread(target = connection_listening_thread, args=(client_socket,address,command_queue,label_q,)).start() #for each socket creating a listening thread

def spawn_command_thread(command_queue,socket_list):
	print("spawn_command_thread started")
	prev_command = {}
	while True:
		while command_queue.qsize() != 0:
			command = ast.literal_eval(command_queue.get())[1]
			#print(f"getting command < {command} > ")
			if command not in prev_command.keys():
				prev_command[command] = 1
			else:
				prev_command[command] +=1
			#print(f"prev command: {prev_command}")
			if int(command.split(' ')[-1]) == prev_command[command]:
				prev_command.pop(command)
				Thread(target = processing_thread, args=(command,socket_list,)).start() #for each

def connection_listening_thread(client_socket,address, command_queue,label_q):
	global IDENTIFIER
	global CONNNECTION_EASTABLISHED
	global device_list
	BUFFER_SIZE = 65536
	NAME_SIZE = 256
	LABEL_SIZE = 256
	MSG_SIZE = 256
	REQUEST_SIZE=1024
	TASK_ID_SIZE=10
	SEPARATOR = "<SEPARATOR>"

	print(f"socket at {address} is being listened")
	
	while True:
		if CONNNECTION_EASTABLISHED == True:
			msg_type = receive_request(1,client_socket).decode()
			print(f"msg: {msg_type}")
			
			# receving file
			if msg_type == 'Q':
				received = int(receive_request(10,client_socket).decode().strip())
				print(f"put {client_socket} with id {received} in queue")
				label_q.put((received,client_socket))
				
			elif msg_type == 'F':
				received = receive_request(NAME_SIZE,client_socket).decode()
				filename, filesize, space = received.split(SEPARATOR)
				# remove absolute path if there is any
				filename = os.path.basename(filename)
				filesize = int(filesize)
				receive_files(filesize,BUFFER_SIZE,filename,client_socket)

			# receiving network test request
			elif msg_type == "P":
				transerr= float(receive_request(10,client_socket).decode().strip())
				print(f"transerr:{transerr}")
				Thread(target=network_speed_test, args=(device_list,transerr,)).start()
				
			# receiving file request 
			elif msg_type == "R":
				file_requested = receive_request(NAME_SIZE,client_socket).decode().strip()
				if os.path.exists(str(file_requested)) == True:
					send_files(client_socket,str(file_requested))
			
			# receiving file size request
			elif msg_type == "S":
				tk_id = client_socket.recv(TASK_ID_SIZE).decode()
				input_request = receive_request(REQUEST_SIZE,client_socket)
				output_request = receive_request(REQUEST_SIZE,client_socket)
				Thread(target=update_size_proc, args=(tk_id, input_request,output_request,client_socket,)).start()	
						
			# receiving command	
			elif msg_type == "C":
				command = receive_request(MSG_SIZE,client_socket).decode()
				priority=ast.literal_eval(command)[0]
				real_command = ast.literal_eval(command)[1]
				command_queue.put(str((priority,real_command)))

			# receiving label of the device
			elif msg_type == "L":
				label= receive_request(NAME_SIZE,client_socket).decode()
				IDENTIFIER = int(label)
				print(f"IDENTIFIER of this device: {IDENTIFIER}")
				CONNNECTION_EASTABLISHED = False
			
			# receiving clean command
			elif msg_type == "X":
				command = receive_request(MSG_SIZE,client_socket).decode().strip()
				p=subprocess.Popen([command],shell=True,stdin=None,stdout=subprocess.PIPE,stderr=subprocess.PIPE,close_fds=True)

			else:
				print(f'transmission error, unrecognizable message type: {msg_type} from {client_socket}, exiting')
				print(client_socket.recv(10))
				sys.exit()
	print("socket closed =======================================")
	client_socket.close()

def processing_thread(command,socket_list):
	global IDENTIFIER
	dependency_dic=json_file_loader("dependency_file.json")
	task_dic=json_file_loader("task_file.json")
	depend_lookup=json_file_loader("depend_lookup.json")
	input_lookup=json_file_loader("input_lookup.json")
	output_lookup=json_file_loader("output_lookup.json")

	print(f"{command.strip()} thread is created")

	# loading all the json files to get the status of the allocation
	allocation_file=command.split(' ')[0]
	tk_num = command.split(' ')[1]
	instance_count=command.split(' ')[2]

	# try load the allocation file, if not available, waiting / re-requesting
	try:
		allocation_dic=json_file_loader(allocation_file)
	except FileNotFoundError:
		start_time = time.time()
		while os.path.exists(allocation_file) == False:
			if time.time() - start_time > 40:
				send_resend_request(socket_list[-1],IDENTIFIER,allocation_file)	#request orchestator resend the allocation file
			if time.time() - start_time > 80:
				print(f"{allocation_file} cannot be found on the device, exiting")
				sys.exit()
	
	#running a check to see if all input files are available; if missing, try to retrieve from replicated services
	for input_file in input_lookup[str(tk_num)]:
		# check non-meta files
		if input_file[1] == 0:					
			if os.path.exists(input_file[0]+input_file[2]):
				pass
			else:																				
				raise FileNotFoundError(errno.ENOENT, os.strerror(errno.ENOENT), input_file[0])

		# check meta files generated by previous tasks
		else:
			file_to_be_retrieved = input_file[0] + str(instance_count) + input_file[2]
			waittime_start=time.time()
			while os.path.exists(file_to_be_retrieved) == False:
				elapsed_time=time.time()
				if elapsed_time - waittime_start > 40:
					break
			if 	os.path.exists(file_to_be_retrieved):
				pass
			else:																				# this meta file is missing, go back to previous stage and fetch
				for each_depend_task in dependency_dic[str(tk_num)]:							# find all dependency of current task
					for each_device in allocation_dic[str(each_depend_task[0])]:				# find the devices that execute those dependent task
						file_suppose_to_produced = output_lookup[each_depend_task[0]]			# find the output files suppose to be produced by those dependent tasks
						for each_file_produced in file_suppose_to_produced:						# check if the missing file is one of them
							if each_file_produced[0] == input_file[0]:
								try:
									print(f"Retrivng {file_to_be_retrieved} from {each_device}")
									send_resend_request(socket_list[each_device],IDENTIFIER,file_to_be_retrieved)
								except:
									print(f"Fail to retrieve missing file {file_to_be_retrieved} from device {each_device}, exiting")
									sys.exit()

				timeout_start = time.time()
				while os.path.exists(file_to_be_retrieved) == False:
					timeout_end=time.time()
					if timeout_end - timeout_start > 70:
						print(f"Time out on retrieving file: {file_to_be_retrieved},exiting")
						sys.exit()

	#execute the main task related to this node
	task = task_lookup(tk_num, task_dic)
	command = execute_main_task(task, instance_count)
	print(command)
	p=subprocess.Popen([command],shell=True,stdin=None,stdout=subprocess.PIPE,stderr=subprocess.PIPE,close_fds=True)
	out,err = p.communicate()

	if err:
		print(f"task {command} did not finish execution, exiting! \n Error: {err}")
		sys.exit()

	# send the output from this task to the edge devices that will execute the depedent tasks
	print("=============================================== sending corresponding tasks")
	output_from_current_tk = output_lookup[str(tk_num)]
	for each in output_from_current_tk:
		intermediate_file = each[0]+str(instance_count)+each[2]
		for each_dest in each[3]:
			for each_edge in allocation_dic[str(each_dest)]:
				# no need to send if on the same device
				if each_edge != IDENTIFIER:
					send_files(socket_list[each_edge],intermediate_file)

	#looking for the dependency and find the next device and task
	next_stage_dict=next_task(tk_num,depend_lookup,input_lookup)
	#print(f"current tk: {tk_num}, next_stage_dict:{next_stage_dict}")

	#if current task is the last task
	if len(next_stage_dict) == 0:
		output_file_list=output_lookup[str(tk_num)]
		for each_output in output_file_list:
			output_file=f"{each_output[0]}{instance_count}{each_output[2]}"
			result_wait_start = time.time()
			while os.path.exists(output_file) == False:
				if time.time() - result_wait_start > 30:
					print(f"{output_file} is not produced with in time limit, exiting!")
					sys.exit()
			send_files(socket_list[-1],output_file)
			print(f"Send result:{output_file} of instance {instance_count} back to orchestrator")

	# send the next command to next stage of tasks
	for each_tk in next_stage_dict.keys():
		allocation_file = "allocation_"+str(instance_count)+".json"
		num_depend = len(dependency_dic[each_tk])
		command = "{} {} {} {}".format(allocation_file,each_tk,instance_count,num_depend)
		command = str((int(instance_count),command))
		for ed in allocation_dic[each_tk]:
			print(f"sending comand ==========: {command}")
			send_command(socket_list[ed],command)


#Running this on each edge
if __name__ =='__main__':
	connection_q = Queue()
	command_q = PriorityQueue()
	label_q = Queue()
	socket_q = Queue()
	socket_list=[]
	CONNNECTION_EASTABLISHED = True

	try:
		Thread(target = connection_creation_thread, args = (connection_q, socket_q)).start()	# constantly colleccting all incoming connections and put them in a connection q
		Thread(target = spawn_listening_thread, args=(connection_q,command_q,label_q,)).start() # for each socket connection in connection queue, creat a listenning thread and listen to command or receive files
		command_thread=Thread(target = spawn_command_thread, args = (command_q,socket_list,)) # reading the command from the queue an spawn thread to execue the command
		
	except:
		print("ERROR")

	# edge_list = json_file_loader(os.path.join(os.getcwd(),"edge_list.json"))
	_curFolder = os.path.dirname(os.path.abspath(__file__))
	edge_list = json_file_loader(os.path.join(_curFolder,"edge_list.json"))

	for i in range(len(edge_list.keys())):
		socket_list.append(None)

	#waiting for the device get assigned with the idetifier
	while IDENTIFIER < 0: pass

	counter = 0
	skip = True
	while counter != len(edge_list.keys())- 1 - IDENTIFIER:
		if socket_q.qsize()!=0: 
			client_socket,address = socket_q.get()
			if skip == True:
				socket_list[-1]=client_socket
				skip=False
			else:
				if label_q.qsize() != 0: 
					print("adddddd 1")
					ident, connected_socket = label_q.get()
					#ident = int(receive_request(10,client_socket).decode().strip())
					socket_list[ident]=connected_socket
				#print(f"address: {address}")
					print(connected_socket)
			#ident = int(list(edge_list.keys())[list(edge_list.values()).index(address[0])])
			counter +=1

	for i in range(IDENTIFIER,-1,-1):
		if i <= IDENTIFIER:
			s = socket_connections(edge_list[str(i)],5001)
			#ident = int(list(edge_list.keys())[list(edge_list.values()).index(edge_list[str(i)])])
			socket_list[i]=s
			send_identifier(s,IDENTIFIER)
			connection_q.put([s,edge_list[str(i)]]) 
	print(socket_list)

	for each_key in edge_list.keys():
		device_list.append(edge_list[each_key])
	
	CONNNECTION_EASTABLISHED = True	

	time.sleep(15)
	while label_q.qsize()!=0:
		ident, connected_socket = label_q.get()
		#ident = int(receive_request(10,client_socket).decode().strip())
		socket_list[ident]=connected_socket

	command_thread.start()

