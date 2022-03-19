import paramiko
from scp import SCPClient

access_dict={}
access_dict[0]="ec2-user@ec2-3-91-202-21.compute-1.amazonaws.com"

#creat EC2 client for dispatching
def createSSHClient(server, port, user, password):
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect("ec2-3-91-202-21.compute-1.amazonaws.com",username='ec2-user', key_filename=password)
    return client

#The dispatch function should be called when one application instance is orchestrated
def dispatch(allocation):
	for each in allocation.keys():
		print(each)

if __name__ =='__main__':
	client=createSSHClient(0, 0, 0, "IBDASH.pem")
	client_1 = SCPClient(client.get_transport())
	client_1.put("helpers.py")
