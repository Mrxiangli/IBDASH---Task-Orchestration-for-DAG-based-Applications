import argparse
import configparser
import json
import subprocess
import sys
import paramiko
from scp import SCPClient
import errno
import socket
import os
from threading import Thread
from queue import Queue
import time

IDENTIFIER = -1 

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


def send_files(s,filename):
	SEPARATOR = "<SEPARATOR>"
	BUFFER_SIZE = 65536 # send 4096 bytes each time step
	NAME_SIZE = 256
	filesize = os.path.getsize(filename)
	name=f"{filename}{SEPARATOR}{filesize}{SEPARATOR}".ljust(NAME_SIZE).encode()
	s.send("F".encode())
	print("blocking?")
	s.send(name)
	print("sending name?")
	counter = 0
	with open(filename, "rb") as f:
		bytes_read = f.read(filesize)
		print("able to read?")
		start = time.time()
		print(s)
		s.sendall(bytes_read)
		print("able to send?")
		end = time.time()
		print(f"{filename}:finishing done: {end-start}")
	s.send("/EOF".encode())


def send_command(s,msg):
	SEPARATOR = "<SEPARATOR>"
	BUFFER_SIZE = 4096 # send 4096 bytes each time step
	MSG_SIZE = 256
	print(msg)
	s.send("C".encode())
	s.send(msg.ljust(MSG_SIZE).encode())


def socket_connections(host,port):
	s = socket.socket()
	print(f"[+] Connecting to {host}:{port}")
	s.connect((host, port))
	s.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
	print("[+] Connected.")
	return s

def connection_creation_thread(connection_queue, socket_q):
	print("gggg")
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
		print(f"size of queue: {connection_queue.qsize()}")

def spawn_listening_thread(connection_queue, command_queue):
	print("sssss")
	while True:
		while connection_queue.qsize() != 0:
			print("waiting for connection queue to be filled")
			client_socket,address = connection_queue.get()
			Thread(target = connection_listening_thread, args=(client_socket,address,command_queue,)).start() #for each socket creating a listening thread

def spawn_command_thread(command_queue,socket_list):
	print("spawn_command_thread started")
	while True:
		while command_queue.qsize() != 0:
			print(f"command queue: {command_queue}")
			command = command_queue.get()
			print(f"getting command < {command} > out")
			Thread(target = processing_thread, args=(command,socket_list,)).start() #for each

def connection_listening_thread(client_socket,address, command_queue):
	global IDENTIFIER
	BUFFER_SIZE = 65536
	NAME_SIZE = 256
	LABEL_SIZE = 256
	MSG_SIZE = 256
	SEPARATOR = "<SEPARATOR>"

	print(f"socket at {address} is being listened")
	
	#print(f"[*] Listening as {SERVER_HOST}:{SERVER_PORT}")

	# if below code is executed, that means the sender is connected
	#print(f"[+] {address} is connected.")
	# for each connection

	while True:
		print(f"{address} listening is alive")
		msg_type = client_socket.recv(1).decode()
		print(f"msg: {msg_type}")
		# if msg_type == "F":
		# 	received = client_socket.recv(NAME_SIZE).decode()
		# 	filename, filesize, space = received.split(SEPARATOR)
		# 	print(f"filename: {filename}")

		# continue
		# if msg_type != "F" and msg_type !="C" and msg_type!="" and msg_type != "L":
		# 	print(f"msg: {msg_type}")
		# 	print(f"socket {client_socket} out of sync")
		if msg_type == 'F':
			print("###########################################")
			start = time.time()
			received = client_socket.recv(NAME_SIZE).decode()
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
				print(f"{filename} is received")
				print(f"time: {end-start}")
				if received_size == filesize:
					bytes_read = client_socket.recv(4)
					if bytes_read.decode() != "/EOF":
						print(f" error transmitting {filename}")

		elif msg_type == "C":
			command = client_socket.recv(MSG_SIZE).decode()
			command_queue.put(command)

		elif msg_type == "L":
			label= client_socket.recv(NAME_SIZE).decode()
			#label=int(label.strip())
			IDENTIFIER = int(label)
			print(f"IDENTIFIER: {IDENTIFIER}")
			#command_queue.put(command)
		
		else:
			print(f'getting shitty packets')

		# close the client socket
		#client_socket.close()
	# close the server socket
	print(f"{address} is closing")
	s.close()

def processing_thread(command,socket_list):
	global IDENTIFIER
	dependency_dic=json_file_loader("dependency_file.json")
	task_dic=json_file_loader("task_file.json")
	depend_lookup=json_file_loader("depend_lookup.json")
	input_lookup=json_file_loader("input_lookup.json")
	output_lookup=json_file_loader("output_lookup.json")
	command = command.split("/EOC")[0]
	print(f"{command.strip()} thread is created")

	#need to source the bashrc file to activate the corresponding conda enviroment
	#stdin,stdout,stderr=edge_list_ssh[ed].exec_command("source ~/.bashrc")

	# loading all the json files to get the status of the allocation
	allocation_file=command.split(' ')[0]
	tk_num = command.split(' ')[1]
	instance_count=command.split(' ')[2]
	allocation_dic=json_file_loader(allocation_file)
	

	#running a check to see if all input files are available; if missing, try to retrieve from replicated service
	for input_file in input_lookup[str(tk_num)]:
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
				for each_depend_task in dependency_dic[str(tk_num)]:							#find all dependency of current task
					for each_device in allocation_dic[str(each_depend_task[0])]:				# find the devices that execute those dependent task
						file_suppose_to_produced = output_lookup[each_depend_task[0]]			# find the output files suppose to be produced by those dependent tasks
						for each_file_produced in file_suppose_to_produced:						# check if the missing file is one of them
							if each_file_produced[0] == input_file[0]:
								try:
									#err=edge_list_scp[int(each_device[0])].get(file_to_be_retrieved)	# send request to retrieve file
									#if not err:
									#	break
									pass
								except:
									pass	

	#execute the main task related to this node
	task = task_lookup(tk_num, task_dic)
	command = execute_main_task(task, instance_count)
	print(command)
	p=subprocess.Popen([command],shell=True,stdin=None,stdout=subprocess.PIPE,stderr=subprocess.PIPE,close_fds=True)
	out,err = p.communicate()
	#print(err)
	if err:
		print("task {} did not finish execution, exiting!".format(task))
		print(err)
		sys.exit()

	output_from_current_tk = output_lookup[str(tk_num)]
	for each in output_from_current_tk:
		print(f"file: {each}")
		intermediate_file = each[0]+str(instance_count)+each[2]
		print(intermediate_file)
		#print(each)
		for each_edge in allocation_dic[str(each[3])]:
			if each_edge != IDENTIFIER:
				print("are we sending?")
				send_files(socket_list[each_edge],intermediate_file)
				print("finish sending?")
			#edge_list_scp[each_edge].put(intermediate_file)
	print("does it reach here?")
	#looking for the dependency and find the next device and task
	next_stage_dict=next_task(tk_num,depend_lookup,input_lookup)
	#print(next_stage_dict)
	#Curent task is the last task
	if len(next_stage_dict) == 0:
		#print(input_lookup['end'])
		output_file=f"predict_{instance_count}.txt"
		send_files(socket_list[-1],output_file)
		print("finish the result")
		#result_file = "predict_"+str(args.ic)+".txt"
		#edge_list_scp[3].put(result_file,"/home/jonny/Documents/Research/IBDASH_V2/result")
	#send the output from this stage to next device

	for each_tk in next_stage_dict.keys():
		ed = allocation_dic[each_tk][0]
		
		allocation_file = "allocation_"+str(instance_count)+".json"
		command = "{} {} {}".format(allocation_file,each_tk,instance_count)
		#print(command)
		#print("the above command execute on ed: {}".format(ed))
		#stdin,stdout,stderr=edge_list_ssh[ed].exec_command(command)
		print("sending comand ==========: {command}")
		send_command(socket_list[ed],command)
		#edge_list_ssh[ed].exec_command(command)
		#for line in stdout.read().splitlines():
		#	print(line)

#Running this on each edge
if __name__ =='__main__':
	connection_q = Queue()
	command_q = Queue()
	socket_q = Queue()
	socket_list=[]
	try:
		Thread(target = connection_creation_thread, args = (connection_q, socket_q)).start()	# constantly colleccting all incoming connections and put them in a connection q
		Thread(target = spawn_listening_thread, args=(connection_q,command_q,)).start() # for each socket connection in connection queue, creat a listenning thread and listen to command or receive files
		command_thread=Thread(target = spawn_command_thread, args = (command_q,socket_list,)) # reading the command from the queue an spawn thread to execue the command
	except:
		print("ERROR")
	
	while os.path.exists("edge_list.json") == False:
		pass
	time.sleep(2)
	edge_list = json_file_loader("edge_list.json")
	while IDENTIFIER < 0: pass
	while len(socket_list) != len(edge_list.keys())- 1 - IDENTIFIER:
		if socket_q.qsize()!=0: 
			client_socket,address = socket_q.get()
			socket_list.insert(0,client_socket)
	for i in range(IDENTIFIER,-1,-1):
		if i <= IDENTIFIER:
			s = socket_connections(edge_list[str(i)],5001)
			socket_list.insert(0,s)
			connection_q.put([s,edge_list[str(i)]]) # this should put 
	command_thread.start()

	#the listening thread is not created


	


