import os.path
import subprocess

instance_count = 10

result_list = []
for i in range(1, instance_count+1):
	file = "predict_{}.txt".format(i)
	result_list.append(file) 

current_dir = os.getcwd()
newdir=os.path.join(current_dir,"result")
timefile=os.path.join(current_dir,"time.txt")
print(newdir)
os.chdir(newdir)
time_list = []

while result_list != []:
	for each in result_list:
		if os.path.exists(each):
			p=subprocess.Popen(["date +%s%N"],shell=True,stdin=None,stdout=subprocess.PIPE,stderr=subprocess.PIPE,close_fds=True)
			out,err = p.communicate()
			result_list.remove(each)
			time_list.append([instance,])
			time_file = open(timefile,"a")
			instance = each.split('_')[1].split('.')[0]
			time_file.write("instance {} end:".format(instance))
			time_file.write(out.decode("utf-8"))
			time_file.close()

