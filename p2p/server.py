import socket
import tqdm
import os
import time
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

# bind the socket to our local address
s.bind((SERVER_HOST, SERVER_PORT))

# enabling our server to accept connections
# 5 here is the number of unaccepted connections that
# the system will allow before refusing new connections
s.listen(5)
print(f"[*] Listening as {SERVER_HOST}:{SERVER_PORT}")
li = []
# accept connection if there is any
while len(li) <4:
	print("again")
	client_socket, address = s.accept() 
	li.append(client_socket)
	print(client_socket)
	print(address)

#time.sleep(10)
#	received = client_socket.recv(BUFFER_SIZE).decode()
#	print(received)
# if below code is executed, that means the sender is connected
print(f"[+] {address} is connected.")
for client_socket in li:
# receive the file infos
# receive using client socket, not server socket
	msg_type = client_socket.recv(1).decode()
	if msg_type == 'F':
		received = client_socket.recv(NAME_SIZE).decode()
		print(received)
		filename, filesize, space = received.split(SEPARATOR)
		# remove absolute path if there is
		filename = os.path.basename(filename)
		# convert to integer
		print("llllllllllllllllllllllll")
		print(filename)
		print("gggggggggggg")
		print(filesize)
		filesize = int(filesize)

		# start receiving the file from the socket
		# and writing to the file stream
		progress = tqdm.tqdm(range(filesize), f"Receiving {filename}", unit="B", unit_scale=True, unit_divisor=1024)
		with open(filename, "wb") as f:
			while True:
				# read 1024 bytes from the socket (receive)
				bytes_read = client_socket.recv(BUFFER_SIZE)
				print("bytes read: {}".format(bytes_read))
				if not bytes_read:    
					# nothing is received
					# file transmitting is done
					break
				# write to the file the bytes we just received
				f.write(bytes_read)
				# update the progress bar
				progress.update(len(bytes_read))
	if msg_type == "C":
		pass
	# close the client socket
	#client_socket.close()
# close the server socket
s.close()
