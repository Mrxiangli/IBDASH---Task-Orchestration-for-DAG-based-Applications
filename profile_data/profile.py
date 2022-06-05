import subprocess
import sys
import numpy as np
import resource
import xlsxwriter

workbook = xlsxwriter.Workbook('ed_mc_light.xlsx')
edm = workbook.add_worksheet("edm")
edc = workbook.add_worksheet("edc")
scale = 1
row = 0
col = 0

cmd = ""
back_pro=[0,1,2,3,4,5,6,7,8]
x_ax = [0,1,2,3,4,5,6,7,8]
#back_pro=[0,1]
#x_ax = [0,1]
prof_num=1
prof_tk = ["pca.py","train_1.py","train_2.py","com_test.py"]
base_tk_list = ["pca.py  &","train_1.py &","train_2.py &","com_test.py &"]
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