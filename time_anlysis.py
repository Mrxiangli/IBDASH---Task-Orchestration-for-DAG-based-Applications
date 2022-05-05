from matplotlib import pyplot as plt
import os
import os.path
import subprocess
import argparse
import configparser

mini=1000000000000000000000
maxi=0
if __name__ =='__main__':
	parser = argparse.ArgumentParser()
	parser.add_argument('--c', type=int, nargs="?")
	parser.add_argument('--f', type=str, nargs="?")
	args = parser.parse_args()
	time_list = [args.f]
	average_latency=[]
	detail_latency=[]
	count = args.c
	for each in time_list:
		latency_dict={}
		scheme_latency=[]

		file = open(each,"r")
		instance = 1
		latency_tot = 0
		while instance < count*2+1:
			time_stamp = file.readline()
			time_stamp = time_stamp.split(":")
			#print(time_stamp)
			first_half = time_stamp[0]
			stamp = int(time_stamp[1])
			if stamp < mini:
				mini = stamp
			if stamp > maxi:
				maxi = stamp
			first_half = first_half.split(" ")
			if first_half[1] not in latency_dict.keys():
				latency_dict[first_half[1]]=[stamp]
			else:
				latency_dict[first_half[1]].append(stamp)
			instance+=1
		print(latency_dict)
		for i in range(1,count+1):
				latency = abs(latency_dict[str(i)][1]-latency_dict[str(i)][0])/1000000000
				#print(latency)
				scheme_latency.append(latency)
				latency_tot += latency
		print("average: {}".format(latency_tot/args.c))
		print(f"throughput: {(maxi-mini)/(1000000000*args.c)}")

"""
fig1, time = plt.subplots(3,2,sharex=True)
fig1.tight_layout()
time[0][0].plot(range(1,51),detail_latency[0],"b", markevery=10,label="service time")
time[0][1].plot(range(1,51),detail_latency[1],"b", markevery=10,label="service time")
time[1][0].plot(range(1,51),detail_latency[2],"b", markevery=10,label="service time")
time[1][1].plot(range(1,51),detail_latency[3],"b", markevery=10,label="service time")
time[2][0].plot(range(1,51),detail_latency[4],"b", markevery=10,label="service time")
time[2][1].plot(range(1,51),detail_latency[5],"b", markevery=10,label="service time")

time[0][0].set_title('IBDASH')
time[0][1].set_title('PETREL')
time[1][0].set_title('LAVEA')
time[1][1].set_title('RR')
time[2][0].set_title('RD')
time[2][1].set_title('LATS')

time[0][0].set_ylabel("service time (s)",fontsize=13)
time[1][0].set_ylabel("service time (s)",fontsize=13)
time[2][0].set_ylabel("service time (s)",fontsize=13)

time[2][1].set_ylabel("instance #",fontsize=13)
time[2][0].set_ylabel("instance #",fontsize=13)
plt.show()

label=["IBDASH","PETREL","LAVEA","RR","RD","LaTS"]
hat = ["x","|",".","+","/","*"]
data = average_latency
plt.xticks(range(len(data)),label)
plt.xlabel('Orchaestration scheme')
plt.ylabel('Average service time (sec)')
plt.title("average service time for 50 application instances")
print(average_latency)
for i in range(len(data)):
	plt.bar(i, data[i], hatch=hat[i]) 
plt.show()
"""