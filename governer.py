import argparse
import configparser
import json
import subprocess
import sys
#import paramiko
#from scp import SCPClient
import errno
import socket
import os
from threading import Thread
from queue import PriorityQueue, Queue
import time
import threading
import ast
from icmplib import ping, multiping
from multiprocessing import Process

IDENTIFIER = -1
device_list=[]

lock = threading.Lock()

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

def network_speed_test(device_list):
	p2p_test=network_test(device_list)
	send_ntwk_test(socket_list[-1],p2p_test,IDENTIFIER)

def network_test(device_list):
	p2p_test={}
	for idx,ip_address in enumerate(device_list):
		result = ping(ip_address,count=5,payload_size=1024,interval=0.05,privileged=False)
		print(f"avg_rtt:{result.avg_rtt}")
		p2p_test[idx]=round(((1024/(result.avg_rtt/2))*1000)/1000000,2)
	return p2p_test

def send_files(s,filename):
	global lock
	SEPARATOR = "<SEPARATOR>"
	BUFFER_SIZE = 65536 # send 4096 bytes each time step
	NAME_SIZE = 256
	filesize = os.path.getsize(filename)
	print(f"{filename} is send at {time.time()}")
	name=f"{filename}{SEPARATOR}{filesize}{SEPARATOR}".ljust(NAME_SIZE).encode()
	lock.acquire()
	s.send("F".encode())
	s.send(name)
	counter = 0
	with open(filename, "rb") as f:
		bytes_read = f.read(filesize)
		start = time.time()
		s.sendall(bytes_read)
		end = time.time()
	s.send("/EOF".encode())
	lock.release()

def receive_files(filesize,BUFFER_SIZE,filename,client_socket):
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

		print(f"{filename} is received")
		if received_size == filesize:
			bytes_read = client_socket.recv(4)
			if bytes_read.decode() != "/EOF":
				print(f" error transmitting {filename}, exiting")
				sys.exit()

def send_command(s,msg):
	SEPARATOR = "<SEPARATOR>"
	BUFFER_SIZE = 4096 # send 4096 bytes each time step
	MSG_SIZE = 256
	print(msg)
	global lock
	lock.acquire()
	s.send("C".encode())
	s.send(msg.ljust(MSG_SIZE).encode())
	lock.release()

def send_ntwk_test(s,p2p_test,identifier):
	BUFFER_SIZE = 4096 # send 4096 bytes each time step
	MSG_SIZE = 256
	global lock
	lock.acquire()
	s.send("T".encode())
	s.send(str(identifier).ljust(MSG_SIZE).encode())
	s.send(str(p2p_test).ljust(MSG_SIZE).encode())
	lock.release()

def send_resend_request(s,identifier,file):
	print(f"retrieving {file}")
	BUFFER_SIZE = 4096 # send 4096 bytes each time step
	MSG_SIZE = 256
	global lock
	lock.acquire()
	s.send("R".encode())
	s.send(str(identifier).ljust(MSG_SIZE).encode())
	s.send(str(file).ljust(MSG_SIZE).encode())
	lock.release()


def socket_connections(host,port):
	s = socket.socket()
	print(f"[+] Connecting to {host}:{port}")
	s.connect((host, port))
	s.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
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
	s = socket.socket()
	s.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
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

def spawn_listening_thread(connection_queue, command_queue):
	print("sssss")
	while True:
		while connection_queue.qsize() != 0:
			print("waiting for connection queue to be filled")
			client_socket,address = connection_queue.get()
			Thread(target = connection_listening_thread, args=(client_socket,address,command_queue,)).start() #for each socket creating a listening thread

def spawn_command_thread(command_queue,socket_list):
	print("spawn_command_thread started")
	prev_command = {}
	while True:
		while command_queue.qsize() != 0:
			print(f"command queue: {command_queue}")
			command = ast.literal_eval(command_queue.get())[1]
			print(f"command: {command}")
			print(f"getting command < {command} > out")
			if command not in prev_command.keys():
				prev_command[command] = 1
			else:
				prev_command[command] +=1
			print(f"split {command.split(' ')[-1]}")
			print(f"prev command: {prev_command}")
			if int(command.split(' ')[-1]) == prev_command[command]:
				Thread(target = processing_thread, args=(command,socket_list,)).start() #for each

def connection_listening_thread(client_socket,address, command_queue):
	global IDENTIFIER
	global CONNNECTION_EASTABLISHED
	global device_list
	BUFFER_SIZE = 65536
	NAME_SIZE = 256
	LABEL_SIZE = 256
	MSG_SIZE = 256
	SEPARATOR = "<SEPARATOR>"

	print(f"socket at {address} is being listened")
	
	while True:
		if CONNNECTION_EASTABLISHED == True:
			msg_type = client_socket.recv(1).decode()
			print(f"msg: {msg_type}")
			if msg_type == "P":
				p = Process(target=network_speed_test, args=(device_list,))
				p.start()
				p.join()

			elif msg_type == "R":
				sender_id = client_socket.recv(NAME_SIZE).decode()
				file_requested = client_socket.recv(NAME_SIZE).decode().strip()
				if os.path.exists(str(file_requested)) == True:
					send_files(client_socket,str(file_requested))

			elif msg_type == 'F':
				print("###########################################")
				start = time.time()
				received = client_socket.recv(NAME_SIZE).decode()
				filename, filesize, space = received.split(SEPARATOR)
				# remove absolute path if there is any
				filename = os.path.basename(filename)
				print(f"Receiving file: {received}")
				filesize = int(filesize)
				receive_files(filesize,BUFFER_SIZE,filename,client_socket)
				
			elif msg_type == "C":
				command = client_socket.recv(MSG_SIZE).decode()
				priority=ast.literal_eval(command)[0]
				real_command = ast.literal_eval(command)[1]
				command_queue.put(str((priority,real_command)))

			elif msg_type == "L":
				label= client_socket.recv(NAME_SIZE).decode()
				IDENTIFIER = int(label)
				print(f"IDENTIFIER of this device: {IDENTIFIER}")
				CONNNECTION_EASTABLISHED = False

			else:
				print(f'transmission error, unrecognizable message type: {msg_type}, exiting')
				sys.exit()

	client_socket.close()

def processing_thread(command,socket_list):
	global IDENTIFIER
	dependency_dic=json_file_loader("dependency_file.json")
	task_dic=json_file_loader("task_file.json")
	depend_lookup=json_file_loader("depend_lookup.json")
	input_lookup=json_file_loader("input_lookup.json")
	output_lookup=json_file_loader("output_lookup.json")
	#command = command.split("/EOC")[0]
	print(f"{command.strip()} thread is created")

	# loading all the json files to get the status of the allocation
	allocation_file=command.split(' ')[0]
	tk_num = command.split(' ')[1]
	instance_count=command.split(' ')[2]

	try:
		allocation_dic=json_file_loader(allocation_file)
	except FileNotFoundError:
		print(f"{allocation_file} cannot be found on the device, exiting")
		sys.exit()
	
	#running a check to see if all input files are available; if missing, try to retrieve from replicated service
	for input_file in input_lookup[str(tk_num)]:
		# check non-meta files
		if input_file[1] == 0:					
			if os.path.exists(input_file[0]):
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
		print(f"task {task} did not finish execution, exiting! \n Error: {err}")
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
	print(f"current tk: {tk_num}, next_stage_dict:{next_stage_dict}")

	#if current task is the last task
	if len(next_stage_dict) == 0:
		output_file_list=output_lookup[str(tk_num)]
		for each_output in output_file_list:
			output_file=f"{each_output[0]}{instance_count}{each_output[2]}"
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
	socket_q = Queue()
	socket_list=[]
	CONNNECTION_EASTABLISHED = True

	try:
		Thread(target = connection_creation_thread, args = (connection_q, socket_q)).start()	# constantly colleccting all incoming connections and put them in a connection q
		Thread(target = spawn_listening_thread, args=(connection_q,command_q,)).start() # for each socket connection in connection queue, creat a listenning thread and listen to command or receive files
		command_thread=Thread(target = spawn_command_thread, args = (command_q,socket_list,)) # reading the command from the queue an spawn thread to execue the command
		
	except:
		print("ERROR")

	edge_list = json_file_loader("edge_list.json")
	for i in range(len(edge_list.keys())):
		socket_list.append(None)
	while IDENTIFIER < 0: pass
	counter = 0
	while counter != len(edge_list.keys())- 1 - IDENTIFIER:
		if socket_q.qsize()!=0: 
			client_socket,address = socket_q.get()
			ident = int(list(edge_list.keys())[list(edge_list.values()).index(address[0])])
			socket_list[ident]=client_socket
			counter +=1
	for i in range(IDENTIFIER,-1,-1):
		if i <= IDENTIFIER:
			s = socket_connections(edge_list[str(i)],5001)
			ident = int(list(edge_list.keys())[list(edge_list.values()).index(edge_list[str(i)])])
			socket_list[ident]=s
			connection_q.put([s,edge_list[str(i)]]) # this should put 

	
	for each_key in edge_list.keys():
		device_list.append(edge_list[each_key])

	command_thread.start()
	CONNNECTION_EASTABLISHED = True





	


