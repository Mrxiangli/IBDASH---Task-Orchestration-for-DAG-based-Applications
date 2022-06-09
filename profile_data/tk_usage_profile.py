import psutil
import subprocess
import sys
import numpy as np
import resource
import time
from xlwt import Workbook
import random
import threading

from queue import Queue

def cpu_task(queue):
	ct=0
	total=0
	print("starting thread")
	while queue.empty() is False:
		current_cpu = psutil.cpu_percent(interval=0.1)
		if current_cpu > 1.0 :
			print(current_cpu)
			total += current_cpu
			ct+=1
	print("out")
	cpu_usage = total/ct
	queue.put(cpu_usage)
	print(cpu_usage)

if __name__ == "__main__":

	# Workbook is created
	wb = Workbook()
	queue=Queue()
	# add_sheet is used to create sheet.
	ed0 = wb.add_sheet('ed0_usage')
	  
	ed0.write(0, 0, '#tk0')
	ed0.write(0, 1, '#tk1')
	ed0.write(0, 2, '#tk2')
	ed0.write(0, 3, '#tk3')
	# ed0.write(0, 4, '#tk4')
	# ed0.write(0, 5, '#tk5')
	# ed0.write(0, 6, '#tk6')
	# ed0.write(0, 7, '#tk7')
	ed0.write(0, 4, 'cpu_usage')

	prof_tk = ["pca.py","train_1.py","train_2.py","com_test.py"]
	tk_dict={}
	num_select = 1
	for row in range(1,100):
		print("processing row: "+str(row))
		cmd=""
		for each in prof_tk:
			tk_dict[each] = 0

		for i in range(0,num_select):
			tk = random.randrange(0,4,1)
			tk_dict[prof_tk[tk]]+=1
			cmd += "python " + prof_tk[tk]+ "& "
		for j in range(0,4):
			ed0.write(row,j,tk_dict[prof_tk[j]])
		queue.put('s')
		t1 = threading.Thread(target=cpu_task, args=(queue,))
		t1.start()
		prof_proc = subprocess.check_output([cmd],shell=True,encoding='utf8')
		queue.get()
		while queue.empty():
			time.sleep(1)
			print("stuck1")
			pass
		ed0.write(row,4,queue.get())
		t1.join()
		num_select =num_select%10+1

wb.save('light_cpu_usage.xls')
