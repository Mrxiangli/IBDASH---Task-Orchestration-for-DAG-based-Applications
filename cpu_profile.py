import subprocess
import sys
import numpy as np
import resource

cmd = ""
cpu_limit=[100, 80, 50, 30 ,10, 5]
prof_tk = ["video_split.py -f test.mp4 -s 10", "extract_frame_1.py", "extract_frame_2.py", "img_class_1.py","img_class_2.py"]
mc_dic={}
for profile_file in prof_tk:
	time_plot = []
	for limit in cpu_limit:
		cmd="cpulimit -l "+ str(limit) + " python "+ profile_file
		print(cmd)
		prof_proc = subprocess.Popen([cmd],shell=True,stdout=subprocess.PIPE,encoding='utf8')
		output = prof_proc.stdout.read()
		print(output)
		time_plot.append(output.split(" ")[1])
	mc_dic[profile_file]=time_plot
print(mc_dic)