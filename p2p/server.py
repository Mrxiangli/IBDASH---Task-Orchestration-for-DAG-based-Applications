import socket
import tqdm
import os
import time
import pdb
import sys
# device's IP address
SERVER_HOST = "0.0.0.0"
SERVER_PORT = 5001
# receive 4096 bytes each time
BUFFER_SIZE = 4096
SEPARATOR = "<SEPARATOR>"
NAME_SIZE = 256
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
print(f"[*] Listening as {SERVER_HOST}:{SERVER_PORT}")
li = []
# accept connection if there is any
while len(li)<1:
	print("again")
	#pdb.set_trace()
	client_socket, address = s.accept() 
	li.append(client_socket)
	print(client_socket)
	print(address)

# if below code is executed, that means the sender is connected
print(f"[+] {address} is connected.")
# for each connection
for client_socket in li:
# receive the file infos
# receive using client socket, not server socket
	while True:
		msg_type = client_socket.recv(1).decode()
		if msg_type == 'F':
			received = client_socket.recv(NAME_SIZE).decode()
			print(received)
			filename, filesize, space = received.split(SEPARATOR)
			# remove absolute path if there is
			filename = os.path.basename(filename)
			# convert to integer
			filesize = int(filesize)
			

			# start receiving the file from the socket
			# and writing to the file stream
			#progress = tqdm.tqdm(range(filesize), f"Receiving {filename}", unit="B", unit_scale=True, unit_divisor=1024)
			received_size = 0
			count = 0
			with open(filename, "wb") as f:
				while (filesize - received_size) > BUFFER_SIZE:
					
					bytes_read = client_socket.recv(BUFFER_SIZE)
					received_size += len(bytes_read.decode())
					f.write(bytes_read)
				residue = filesize - received_size
				while residue > 0:
					bytes_read = client_socket.recv(1)
					received_size += len(bytes_read.decode())
					f.write(bytes_read)
					residue -=1
				if received_size == filesize:
					bytes_read = client_socket.recv(4)
					if bytes_read.decode() != "/EOF":
						print(f" error transmitting {filename}")

		if msg_type == "C":
			command = client_socket.recv(BUFFER_SIZE).decode()
			print(command)
			#print(command)
		# close the client socket
		#client_socket.close()
	# close the server socket
	s.close()
