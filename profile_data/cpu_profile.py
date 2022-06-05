import subprocess
import sys
import numpy as np
import resource
import xlsxwriter

workbook = xlsxwriter.Workbook('cpu_lat_light.xlsx')
usage_lat = workbook.add_worksheet("lat_us")
row = 0


cmd = ""
cpu_limit=[100, 80, 50, 30 ,10, 5]
#cpu_limit=[100]
prof_tk = prof_tk = ["pca.py","train_1.py","train_2.py","com_test.py"]
mc_dic={}
for profile_file in prof_tk:
	time_plot = []
	for limit in cpu_limit:
		cmd="cpulimit -l "+ str(limit) + " -q python "+ profile_file
		print(cmd)
		prof_proc = subprocess.Popen([cmd],shell=True,stdout=subprocess.PIPE,encoding='utf8')
		output = prof_proc.stdout.read()
		print(output)
		time_plot.append(output.split(" ")[1])
	mc_dic[profile_file]=time_plot

	for idx, each in enumerate(time_plot):
		usage_lat.write(row,idx, round(float(each),0))
	row+=1
print(mc_dic)
workbook.close()