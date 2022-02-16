import subprocess
import sys
import numpy as np
import resource

cmd = ""
back_pro=[0,1,2,3,4]
x_ax = [0,1,2,3,4]
prof_num=1
prof_tk = ["video_split.py -f test.mp4 -s 10", "extract_frame_1.py", "extract_frame_2.py", "img_class_1.py","img_class_2.py"]
base_tk = "img_class_2.py & "
mc_dic={}
for profile_file in prof_tk:
	time_plot = []
	for base_num in back_pro:
		for i in range(0,base_num):
			cmd+="python "+ base_tk
		for i in range(0,prof_num):
			cmd+="python "+ profile_file
		print(cmd)
		prof_proc = subprocess.Popen([cmd],shell=True,stdout=subprocess.PIPE,encoding='utf8')
		output = prof_proc.stdout.read()
		print(output)
		time_result = output.split("\n")
		cmd =""
		for each in time_result:
			if profile_file.split(".")[0] in each:
				time_plot.append(float(each.split(" ")[1]))
				print(time_plot)
				break
	z1 = np.polyfit(x_ax,time_plot,1)
	mc_dic[profile_file]=z1
print(mc_dic)



