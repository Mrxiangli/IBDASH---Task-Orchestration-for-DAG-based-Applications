import subprocess
import sys
import numpy as np
import resource
import xlsxwriter

workbook = xlsxwriter.Workbook('t2.xlsx')
edm = workbook.add_worksheet("ED_m")
edc = workbook.add_worksheet("ED_c")
scale = 1
row = 0
col = 0

cmd = ""
back_pro=[0,1,2,3,4,5,6,7,8]
x_ax = [0,1,2,3,4,5,6,7,8]
prof_num=1
prof_tk = ["input_split.py --count 0", "map1.py --count 0",  "map2.py --count 0",  "map3.py --count 0","map4.py --count 0", "reduce1.py --count 0", "reduce2.py --count 0", "combine.py --count 0"]
base_tk_list = ["input_split.py --count 0 &", "map1.py --count 0 &",  "map2.py --count 0 &",  "map3.py --count 0 &","map4.py --count 0 &", "reduce1.py --count 0 &", "reduce2.py --count 0 &", "combine.py --count 0 &"]
for base_tk in base_tk_list:
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
			time_result = output.split("\n")
			cmd =""
			for each in time_result:
				if profile_file.split(".")[0] in each:
					time_plot.append(float(each.split(" ")[1]))
					print(time_plot)
					break
		z1 = np.polyfit(x_ax,time_plot,1)
		mc_dic[profile_file]=z1
	for each in prof_tk:
		coef = mc_dic[each]
		edm.write(row,col,round(coef[0]*scale,0))
		edc.write(row,col,round(coef[1]*scale,0))
		col+=1
workbook.close()			