from helpers import dag_linearization
from helpers import plot as dagplot
from pathlib import Path
import numpy as np
import pandas as pd
import pathlib
from itertools import chain, combinations
from functools import reduce
from matplotlib import pyplot as plt
from matplotlib.animation import FuncAnimation
from cvxopt import matrix, solvers
from sklearn.cluster import KMeans
import time
from scipy import spatial
import random
from kneed import KneeLocator
import argparse
import math
import csv
import configparser
import logging
import os
import sys
import time as timer
from enum import Enum
from helpers import insert_edge_device, insert_task, app_stage, task_info
import pprint
import matplotlib.pyplot as plt
import math
import random
pp = pprint.PrettyPrinter(indent=4)

if __name__ =='__main__':
	# Opening JSON file that contains the application dag
	f = open('app_config.json',)
	original_dag, linear_dags, vertices, edge_adj = dag_linearization(f)
	task_dict=task_info(vertices)
	dagplot(original_dag)
	vert_dict, vert_stage = app_stage(edge_adj)
	pp.pprint(task_dict)
	pp.pprint(vert_stage)
	
	linear_list = []
	for each in linear_dags:
		li=[]
		for edge in each:
			if edge[1] != "out":
				li.append(edge[1])
		linear_list.append(li)

	path_parent = os.path.dirname(os.getcwd())
	file_path="data/Ed_mc.xlsx"  
	EDmc_path=os.path.join(path_parent,file_path)

	# The following parameters can be used to tune the simulation

	ntbd = 600						#network bandwidth
	app_inst_time = 175				#the period of time that application instances might arrive
	sim_time = 250					#simulation period
	num_arrivals = 150				#number of application instances arrived during app_ins_time	
	pF_thrs = 0.25					#probability of failure threshold
	num_rep = 3						#maximum number of replication allowed
	weight = 0.5

	task_time = random.sample(range(1,app_inst_time),num_arrivals)
	task_time = sorted(task_time)

	task_types = 6					#number of tasks in DAG
	num_edge_1 = 8					#number of edge devices in DAG

	orch_time_ibot=[]
	orch_time_pet =[]
	orch_time_lav =[]
	orch_time_rr=[]
	orch_time_rd=[]
	append_idx = 0

	for edge_index in range(7,num_edge_1):

		num_edge = edge_index+1
		# loading ED_m, ED_c pairs 
		ED_m = np.array(pd.read_excel(EDmc_path,engine="openpyxl",sheet_name="edm",skiprows=0, nrows= num_edge))
		ED_c = np.array(pd.read_excel(EDmc_path,engine="openpyxl",sheet_name="edc",skiprows=0, nrows= num_edge))

		#probabily of failure for each edge device (used expotential distribution for simulation)
		lam=1
		lam2=[0.0003, 0.0023, 0.0023, 0.0024, 0.0025, 0.00032, 0.00011, 0.000031]
		print(lam2)
		pf_ed = [0 for i in range(sim_time) for j in range(num_edge)]
		pf_ed_tk = [0 for i in range(sim_time) for j in range(num_edge)]
		pf_time = np.arange(0, sim_time, 1)

		for i in range(num_edge):
			pf_ed[i]= lam * np.exp(-1*lam2[i]*pf_time)
			pf_ed_tk[i]= 1-lam * np.exp(-1*lam2[i]*pf_time)

	
		#plt.title("Probabily of Failure of EDs")
		#plt.show()
		
		ibot_av_pf=[]
		petrel_av_pf=[]
		lavea_av_pf=[]
		rr_av_pf=[]
		rd_av_pf=[]

		# a dictionary that used to track the available resource on each edge device
		edge_info=dict()
		for i in range(num_edge) :
			edge_info[i]={"total": 10000, "available": 4000}

		# a dictionary that used to track the available models on each edge device	
		model_info=dict()
		for i in range(num_edge):
			model_info[i]=[]



		######### IBOT-PI ###################

		clock_time = np.arange(0,sim_time,1)
		schedule_time_ibot = 0

		ED_tasks = [[[0 for i in range(len(clock_time))] for j in range(num_edge)] for k in range(task_types) ]

		k=0
		i=0
		rp=0
		service_time=[]

		for time in clock_time:
			time = round(time,2)
			if time not in task_time:
				k+=1					# use k to track the unit time 
			else:
				i=0
				#print("==========application instance at time {} starts scheduling=======".format(time))
				allocation=[[] for nd in range(num_edge)]
				start_time = timer.time()
				ibot_pf = 1
				for stage in vert_stage:			# go through each stage in the dag
					longest_task_time=0
					for each_task in vert_stage[stage]:			#go through each task in each stage
						fail_prev_queue = []
						t_pred=sys.maxsize
						ED_pred = 0
						for j in range(num_edge):				#go through all the edge devices
							model_upload_t = 0
							task=int(each_task)
							#print("task: "+str(task))
							w=ED_m[j][task*task_types:task*task_types+task_types]
							#print(w)
							x=[]		
							for idx in range(task_types):		# go through all task types   overall time complexity V * ed * num*task_type
								x.append(ED_tasks[idx][j][k+i])
							print(x)
							c=ED_c[j][task]
							predict_time = np.dot(w,x)+c 		# this is merely the execution time
							if task_dict[each_task][1][0]!="NULL":	# if a model is needed
								if task_dict[each_task][1] not in model_info[j]:
										model_upload_t = math.ceil(task_dict[each_task][1][1]/ntbd)

							predict_time = predict_time + model_upload_t

							if predict_time < t_pred:		
								t_pred = predict_time
								ED_pred = j
							fail_prev_queue.append([j,predict_time])
						fail_prev_queue=sorted(fail_prev_queue,key=lambda x: x[1])
						fail_prev_queue.pop(0)
						allocation[ED_pred].append(each_task)

						# model uploading process		
						if task_dict[each_task][1] not in model_info[ED_pred] and task_dict[each_task][1][0] != "NULL":			 			# if model is not available need to upload model
							while edge_info[ED_pred]["available"] < task_dict[each_task][1][1]:		# pop the least recent used model until there is enough memory to hold the model
								edge_info[ED_pred]["available"]+= model_info[ED_pred][0][1]
								model_info[ED_pred].pop(0)
							model_info[ED_pred].append(task_dict[each_task][1])
						else:
							if task_dict[each_task][1][0] != "NULL":
								model_info[ED_pred].append(model_info[ED_pred].pop(model_info[ED_pred].index(task_dict[each_task][1])))


						# update the total execution latency
						if t_pred > longest_task_time:
							longest_task_time=t_pred

						# update the tasks running on each edge device	
						for j in range(k+i, k+i+t_pred):	
							ED_tasks[task][ED_pred][j]+=1

						#Calculating the probability of current placement
						ProbF = 1 - sum(pf_ed[ED_pred][k+i:k+i+t_pred])/t_pred
						#weighed decision
						weighted_decision = weight*t_pred+(1-weight)*ProbF 
						#print("probability of failue of ED "+str(ED_pred)+" at time "+str(time)+" to time "+str(k+i)+" is "+str(ProbF))
						replication = 0
						while ProbF > pF_thrs and replication < num_rep and fail_prev_queue:		# while the pf > pf_thre and replication < rep_num
							next_opt = fail_prev_queue.pop(0)
							t_next_pred = next_opt[1]
							t_next_ed = next_opt[0]
							new_ProbF = ProbF*(1-sum(pf_ed[t_next_ed][k+i:k+i+t_next_pred])/t_next_pred)
							if  weight*t_next_pred+(1-weight)*new_ProbF < weighted_decision:
								ProbF=new_ProbF
								weighted_decision = weight*t_next_pred+(1-weight)*ProbF
								allocation[t_next_ed].append(each_task)
								replication+=1
								if t_next_pred > longest_task_time:
									longest_task_time=t_next_pred
								for j in range(k+i, k+i+t_next_pred):
									ED_tasks[task][t_next_ed][j]+=1
						ibot_pf = ibot_pf*(1-ProbF)

					i=i+longest_task_time	# tracking the end to end latency
				end_time = timer.time()
				schedule_time_ibot += end_time - start_time
				service_time.append(i+1)
				k=k+1
				#pp.pprint(allocation)
				ibot_av_pf.append(ibot_pf)
		average_service_time_ibot = sum(service_time)/num_arrivals		
		service_time_x = []
		time_x = []
		load_ed = [0 for i in range(sim_time) for j in range(num_edge)]
		for each in range(0,sim_time):
			if each in task_time:
				service_time_x.append(service_time.pop(0))
				time_x.append(each)
			
		for i in range(num_edge):
			for j in range(task_types):
				load_ed[i] = np.add(load_ed[i],ED_tasks[j][i])
		fig1, axs = plt.subplots(5,sharex=True,figsize=(10,14))
		fig1, orch = plt.subplots(1,sharex=True,figsize=(10,6))
		orch.plot(time_x,service_time_x, "*-", markevery=10,label="IBOT-PI")
		orch.title.set_text("Application instance service time")
		orch.set(ylabel="service time (unit time)")
		orch.set(xlabel="Application instance arrival time (unit time)")

		axs[0].plot(range(sim_time),load_ed[0],'-b' ,label="ED0")
		axs[0].title.set_text("IBOT")	
		axs[0].plot(range(sim_time),load_ed[1],'-r', label="ED1")
		axs[0].plot(range(sim_time),load_ed[2],'-g', label="ED2")
		axs[0].set(ylabel="# tasks")
		axs[0].plot(range(sim_time),load_ed[3],'-c' , label="ED3")
		axs[0].plot(range(sim_time),load_ed[4],'-m', label="ED4")
		axs[0].plot(range(sim_time),load_ed[5],'-k', label="ED5")
		axs[0].plot(range(sim_time),load_ed[6],'-y' , label="ED6")
		axs[0].plot(range(sim_time),load_ed[7],'-.b', label="ED7")
		axs[0].legend(loc="upper right")

		plt.subplots_adjust(left=0.1,bottom=0.1,right=0.9,top=0.9,hspace=0.4) 

		
		########## Petrel ############
		model_info=dict()
		
		for i in range(num_edge):
			model_info[i]=[]

		clock_time = np.arange(0,sim_time,1)

		ED_tasks = [[[0 for i in range(len(clock_time))] for j in range(num_edge)] for k in range(task_types) ]
		schedule_time_petrel =0
		k=0
		i=0
		rp=0
		service_time_petrel=[]
		for time in clock_time:
			time = round(time,2)
			if time not in task_time:
				k+=1					# use k to track the unit time 
			else:
				i=0
				start_time = timer.time()
				petrel_pf = 1
				for stage in vert_stage:			# go through each stage in the dag
					longest_task_time=0
					for each_task in vert_stage[stage]:			#go through each task in each stage
						t_pred=sys.maxsize
						ED_pred = 0
						two_edge = [random.randint(0,num_edge-1), random.randint(0,num_edge-1)]	#random pick two edge
					#	print(two_edge)petrel_pf=1
						for j in two_edge:				#go through all the edge devices
							model_upload_t = 0
							task=int(each_task)
							w=ED_m[j][task*task_types:task*task_types+task_types]
							x=[]		
							for idx in range(task_types):		# go through all task types   overall time complexity V * ed * num*task_type
								x.append(ED_tasks[idx][j][k+i])
							c=ED_c[j][task]
							predict_time = np.dot(w,x)+c 		# this is merely the execution time
							if task_dict[each_task][1][0]!="NULL":	# if a model is needed
								if task_dict[each_task][1] not in model_info[j]:
										model_upload_t = math.ceil(task_dict[each_task][1][1]/ntbd)

							predict_time = predict_time + model_upload_t
							if predict_time < t_pred:		
								t_pred = predict_time
								ED_pred = j
						ProbF = 1 - sum(pf_ed[ED_pred][k+i:k+i+t_pred])/t_pred
						petrel_pf=petrel_pf*(1-ProbF)
							# model uploading process		
						if task_dict[each_task][1] not in model_info[ED_pred] and task_dict[each_task][1][0] != "NULL":			 			# if model is not available need to upload model
							while edge_info[ED_pred]["available"] < task_dict[each_task][1][1]:		# pop the least recent used model until there is enough memory to hold the model
								edge_info[ED_pred]["available"]+= model_info[ED_pred][0][1]
								model_info[ED_pred].pop(0)
							model_info[ED_pred].append(task_dict[each_task][1])
						#	pp.pprint(model_info)
						else:
							if task_dict[each_task][1][0] != "NULL":
								model_info[ED_pred].append(model_info[ED_pred].pop(model_info[ED_pred].index(task_dict[each_task][1])))

							# update the total execution latency
						if t_pred > longest_task_time:
							longest_task_time=t_pred
						# update the tasks running on each edge device	
						for j in range(k+i, k+i+t_pred):	
							ED_tasks[task][ED_pred][j]+=1
					i=i+longest_task_time	# tracking the end to end latency
				end_time = timer.time()
				schedule_time_petrel += end_time - start_time
				#print("==========application instance at time {} is done with scheduling=======".format(time))
				service_time_petrel.append(i+1)
				k=k+1
				petrel_av_pf.append(petrel_pf)
		average_service_time_petrel = sum(service_time_petrel)/num_arrivals	
		service_time_x_petrel = []
		time_x_petrel = []
		load_ed_petrel = [0 for i in range(sim_time) for j in range(num_edge)]
		for each in range(0,sim_time):
			if each in task_time:
				service_time_x_petrel.append(service_time_petrel.pop(0))
				time_x_petrel.append(each)
			
		for i in range(num_edge):
			for j in range(task_types):
				load_ed_petrel[i] = np.add(load_ed_petrel[i],ED_tasks[j][i])
		
		orch.plot(time_x_petrel,service_time_x_petrel, ">-", markevery=10,label="PETREL")
		axs[1].plot(range(sim_time),load_ed_petrel[0],'-b' ,label="ED0")
		axs[1].plot(range(sim_time),load_ed_petrel[1],'-r', label="ED1")
		axs[1].plot(range(sim_time),load_ed_petrel[2],'-g', label="ED2")
		axs[1].set(ylabel="# tasks")
		axs[1].title.set_text("PETREL")
		axs[1].plot(range(sim_time),load_ed_petrel[3],'-c' , label="ED3")
		axs[1].plot(range(sim_time),load_ed_petrel[4],'-m', label="ED4")
		axs[1].plot(range(sim_time),load_ed_petrel[5],'-k', label="ED5")
		axs[1].plot(range(sim_time),load_ed_petrel[6],'-y', label="ED6")
		axs[1].plot(range(sim_time),load_ed_petrel[7],'-.b', label="ED7")
		axs[1].legend(loc="upper right")
		plt.subplots_adjust(left=0.1,bottom=0.1,right=0.9,top=0.9,hspace=0.4) 
	
		
		########## LAVEA ############
		model_info=dict()
		for i in range(num_edge):
			model_info[i]=[]

		clock_time = np.arange(0,sim_time,1)

		ED_tasks = [[[0 for i in range(len(clock_time))] for j in range(num_edge)] for k in range(task_types) ]

		k=0
		i=0
		rp=0
		schedule_time_lavea = 0
		service_time_lavea=[]
		for time in clock_time:
			time = round(time,2)
			if time not in task_time:
				k+=1					# use k to track the unit time 
			else:
				i=0
				start_time = timer.time()
				lavea_pf = 1
				for stage in vert_stage:			# go through each stage in the dag
					longest_task_time=0
					for each_task in vert_stage[stage]:			#go through each task in each stage
						t_pred=sys.maxsize
						ED_pred = 0
						num_task_min = sys.maxsize
						for j in range(num_edge):				#go through all the edge devices find the one has least number of tasks
							num_task_on_ed = 0
							for tk in range(task_types):
								num_task_on_ed += ED_tasks[tk][j][time]
							#print("num_tasks on ed " + str(j) + "at time "+ str(time) + "is" + str(num_task_on_ed))
							if num_task_on_ed < num_task_min:
								num_task_min = num_task_on_ed
								ED_pred = j


						model_upload_t = 0
						task=int(each_task)
						w=ED_m[ED_pred][task*task_types:task*task_types+task_types]
						x=[]		
						for idx in range(task_types):		# go through all task types   overall time complexity V * ed * num*task_type
							x.append(ED_tasks[idx][ED_pred][k+i])
						c=ED_c[ED_pred][task]
						predict_time = np.dot(w,x)+c 		# this is merely the execution time
						#pp.pprint(task_dict)
						if task_dict[each_task][1][0]!="NULL":	# if a model is needed
							if task_dict[each_task][1] not in model_info[ED_pred]:
									model_upload_t = math.ceil(task_dict[each_task][1][1]/ntbd)

						predict_time = predict_time + model_upload_t
						t_pred = predict_time

						ProbF = 1 - sum(pf_ed[ED_pred][k+i:k+i+t_pred])/t_pred
						lavea_pf=lavea_pf*(1-ProbF)
							# model uploading process		
						if task_dict[each_task][1] not in model_info[ED_pred] and task_dict[each_task][1][0] != "NULL":			 			# if model is not available need to upload model
							while edge_info[ED_pred]["available"] < task_dict[each_task][1][1]:		# pop the least recent used model until there is enough memory to hold the model
								edge_info[ED_pred]["available"]+= model_info[ED_pred][0][1]
								model_info[ED_pred].pop(0)
							model_info[ED_pred].append(task_dict[each_task][1])
							#pp.pprint(model_info)
						else:
							if task_dict[each_task][1][0] != "NULL":
								model_info[ED_pred].append(model_info[ED_pred].pop(model_info[ED_pred].index(task_dict[each_task][1])))

							# reduce the probability of failure 


							# update the total execution latency
						if t_pred > longest_task_time:
							longest_task_time=t_pred
						# update the tasks running on each edge device	
						for j in range(k+i, k+i+t_pred):
							ED_tasks[task][ED_pred][j]+=1
					i=i+longest_task_time	# tracking the end to end latency
				end_time = timer.time()
				schedule_time_lavea +=end_time - start_time
				#print("==========application instance at time {} is done with scheduling=======".format(time))
				service_time_lavea.append(i+1)
				k=k+1
				lavea_av_pf.append(lavea_pf)
		average_service_time_lavea = sum(service_time_lavea)/num_arrivals	
		service_time_x_lavea = []
		time_x_lavea = []
		load_ed_lavea = [0 for i in range(sim_time) for j in range(num_edge)]
		for each in range(0,sim_time):
			if each in task_time:
				service_time_x_lavea.append(service_time_lavea.pop(0))
				time_x_lavea.append(each)
			
		for i in range(num_edge):
			for j in range(task_types):
				load_ed_lavea[i] = np.add(load_ed_lavea[i],ED_tasks[j][i])

		
		orch.plot(time_x_lavea,service_time_x_lavea,"X-", markevery=10,label="LAVEA")
		axs[2].plot(range(sim_time),load_ed_lavea[0],'-b' ,label="ED0")
		axs[2].plot(range(sim_time),load_ed_lavea[1],'-r', label="ED1")
		axs[2].plot(range(sim_time),load_ed_lavea[2],'-g', label="ED2")
		axs[2].set(ylabel="# tasks")
		axs[2].title.set_text("LAVEA")
		axs[2].plot(range(sim_time),load_ed_lavea[3],'-c' , label="ED3")
		axs[2].plot(range(sim_time),load_ed_lavea[4],'-m', label="ED4")
		axs[2].plot(range(sim_time),load_ed_lavea[5],'-k', label="ED5")
		axs[2].plot(range(sim_time),load_ed_lavea[6],'-y', label="ED5")
		axs[2].plot(range(sim_time),load_ed_lavea[7],'-.b', label="ED6")
		axs[2].legend(loc="upper right")
		plt.subplots_adjust(left=0.1,bottom=0.1,right=0.9,top=0.9,hspace=0.4)
	


		########## Round Robin ############

		model_info=dict()
		for i in range(num_edge):
			model_info[i]=[]

		clock_time = np.arange(0,sim_time,1)
		schedule_time_rr = 0
		ED_tasks = [[[0 for i in range(len(clock_time))] for j in range(num_edge)] for k in range(task_types) ]

		k=0
		i=0
		rp=0
		rr_ed=1
		service_time_rr=[]
		for time in clock_time:
			time = round(time,2)
			if time not in task_time:
				k+=1					# use k to track the unit time 
			else:
				i=0
				start_time = timer.time()
				rr_pf = 1
				for stage in vert_stage:			# go through each stage in the dag
					longest_task_time=0
					for each_task in vert_stage[stage]:			#go through each task in each stage
						ED_pred = 0
						num_task_max = sys.maxsize
						rr_ed += 1
						rr_ed = rr_ed%num_edge
						ED_pred = rr_ed
						model_upload_t = 0
						task=int(each_task)
						w=ED_m[ED_pred][task*task_types:task*task_types+task_types]
						x=[]		
						for idx in range(task_types):		# go through all task types   overall time complexity V * ed * num*task_type
							x.append(ED_tasks[idx][ED_pred][k+i])
						c=ED_c[ED_pred][task]
						predict_time = np.dot(w,x)+c 		# this is merely the execution time
						#pp.pprint(task_dict)
						if task_dict[each_task][1][0]!="NULL":	# if a model is needed
							if task_dict[each_task][1] not in model_info[ED_pred]:
									model_upload_t = math.ceil(task_dict[each_task][1][1]/ntbd)

						predict_time = predict_time + model_upload_t
						t_pred = predict_time
						ProbF = 1 - sum(pf_ed[ED_pred][k+i:k+i+t_pred])/t_pred
						rr_pf=rr_pf*(1-ProbF)
							# model uploading process		
						if task_dict[each_task][1] not in model_info[ED_pred] and task_dict[each_task][1][0] != "NULL":			 			# if model is not available need to upload model
							while edge_info[ED_pred]["available"] < task_dict[each_task][1][1]:		# pop the least recent used model until there is enough memory to hold the model
								edge_info[ED_pred]["available"]+= model_info[ED_pred][0][1]
								model_info[ED_pred].pop(0)
							model_info[ED_pred].append(task_dict[each_task][1])
							#pp.pprint(model_info)
						else:
							if task_dict[each_task][1][0] != "NULL":
								model_info[ED_pred].append(model_info[ED_pred].pop(model_info[ED_pred].index(task_dict[each_task][1])))

							# update the total execution latency
						if t_pred > longest_task_time:
							longest_task_time=t_pred
						# update the tasks running on each edge device	
						for j in range(k+i, k+i+t_pred):
							ED_tasks[task][ED_pred][j]+=1
					i=i+longest_task_time	# tracking the end to end latency
				end_time = timer.time()
				schedule_time_rr += end_time- start_time
				#print("==========application instance at time {} is done with scheduling=======".format(time))
				service_time_rr.append(i+1)
				k=k+1
				rr_av_pf.append(rr_pf)
		average_service_time_rr = sum(service_time_rr)/num_arrivals	
		service_time_x_rr = []
		time_x_rr = []
		load_ed_rr = [0 for i in range(sim_time) for j in range(num_edge)]
		for each in range(0,sim_time):
			if each in task_time:
				service_time_x_rr.append(service_time_rr.pop(0))
				time_x_rr.append(each)
			
		for i in range(num_edge):
			for j in range(task_types):
				load_ed_rr[i] = np.add(load_ed_rr[i],ED_tasks[j][i])
		
		
		orch.plot(time_x_rr,service_time_x_rr,"o-", markevery=10,label="RR")
		axs[3].plot(range(sim_time),load_ed_rr[0],'-b' ,label="ED0")
		axs[3].plot(range(sim_time),load_ed_rr[1],'-r', label="ED1")
		axs[3].plot(range(sim_time),load_ed_rr[2],'-g', label="ED2")
		axs[3].set(ylabel="# tasks")
		axs[3].title.set_text("Round Robin")
		axs[3].plot(range(sim_time),load_ed_rr[3],'-c' , label="ED3")
		axs[3].plot(range(sim_time),load_ed_rr[4],'-m', label="ED4")
		axs[3].plot(range(sim_time),load_ed_rr[5],'-k', label="ED5")
		axs[3].plot(range(sim_time),load_ed_rr[6],'-y', label="ED5")
		axs[3].plot(range(sim_time),load_ed_rr[7],'-.b', label="ED6")
		axs[3].legend(loc="upper right")
		plt.subplots_adjust(left=0.1,bottom=0.1,right=0.9,top=0.9,hspace=0.4)

	
		

		########## Random ############

		model_info=dict()
		for i in range(num_edge):
			model_info[i]=[]

		clock_time = np.arange(0,sim_time,1)
		schedule_time_rd = 0
		ED_tasks = [[[0 for i in range(len(clock_time))] for j in range(num_edge)] for k in range(task_types) ]

		k=0
		i=0
		rp=0
		service_time_rd=[]
		for time in clock_time:
			time = round(time,2)
			if time not in task_time:
				k+=1					# use k to track the unit time 
			else:
				i=0
				start_time = timer.time()
				rd_pf = 1
				for stage in vert_stage:			# go through each stage in the dag
					longest_task_time=0
					for each_task in vert_stage[stage]:			#go through each task in each stage
						ED_pred = random.randint(0,num_edge-1)
						model_upload_t = 0
						task=int(each_task)
						w=ED_m[ED_pred][task*task_types:task*task_types+task_types]
						x=[]		
						for idx in range(task_types):		# go through all task types   overall time complexity V * ed * num*task_type
							x.append(ED_tasks[idx][ED_pred][k+i])
						c=ED_c[ED_pred][task]
						predict_time = np.dot(w,x)+c 		# this is merely the execution time
						#pp.pprint(task_dict)
						if task_dict[each_task][1][0]!="NULL":	# if a model is needed
							if task_dict[each_task][1] not in model_info[ED_pred]:
									model_upload_t = math.ceil(task_dict[each_task][1][1]/ntbd)

						predict_time = predict_time + model_upload_t
						t_pred = predict_time
						ProbF = 1 - sum(pf_ed[ED_pred][k+i:k+i+t_pred])/t_pred
						rd_pf=rd_pf*(1-ProbF)
							# model uploading process		
						if task_dict[each_task][1] not in model_info[ED_pred] and task_dict[each_task][1][0] != "NULL":			 			# if model is not available need to upload model
							while edge_info[ED_pred]["available"] < task_dict[each_task][1][1]:		# pop the least recent used model until there is enough memory to hold the model
								edge_info[ED_pred]["available"]+= model_info[ED_pred][0][1]
								model_info[ED_pred].pop(0)
							model_info[ED_pred].append(task_dict[each_task][1])
							#pp.pprint(model_info)
						else:
							if task_dict[each_task][1][0] != "NULL":
								model_info[ED_pred].append(model_info[ED_pred].pop(model_info[ED_pred].index(task_dict[each_task][1])))

							# update the total execution latency
						if t_pred > longest_task_time:
							longest_task_time=t_pred
						# update the tasks running on each edge device	
						for j in range(k+i, k+i+t_pred):
							ED_tasks[task][ED_pred][j]+=1
					i=i+longest_task_time	# tracking the end to end latency
				end_time = timer.time()
				schedule_time_rd = end_time - start_time
				#print("==========application instance at time {} is done with scheduling=======".format(time))
				service_time_rd.append(i+1)
				k=k+1
				rd_av_pf.append(rd_pf)
		average_service_time_rd = sum(service_time_rd)/num_arrivals	
		service_time_x_rd= []
		time_x_rd = []
		load_ed_rd = [0 for i in range(sim_time) for j in range(num_edge)]
		for each in range(0,sim_time):
			if each in task_time:
				service_time_x_rd.append(service_time_rd.pop(0))
				time_x_rd.append(each)
			
		for i in range(num_edge):
			for j in range(task_types):
				load_ed_rd[i] = np.add(load_ed_rd[i],ED_tasks[j][i])

	
		
		print(average_service_time_ibot)
		print(average_service_time_petrel)
		print(average_service_time_lavea)
		print(average_service_time_rr)
		print(average_service_time_rd)

		orch.plot(time_x_rd,service_time_x_rd,"<-", markevery=10,label="Random")
		axs[4].plot(range(sim_time),load_ed_rd[0],'-b' ,label="ED0")
		axs[4].plot(range(sim_time),load_ed_rd[1],'-r', label="ED1")
		axs[4].plot(range(sim_time),load_ed_rd[2],'-g', label="ED2")
		axs[4].set(ylabel="# tasks")
		axs[4].title.set_text("Random")
		axs[4].plot(range(sim_time),load_ed_rd[3],'-c' , label="ED3")
		axs[4].plot(range(sim_time),load_ed_rd[4],'-m', label="ED4")
		axs[4].plot(range(sim_time),load_ed_rd[5],'-k', label="ED5")
		axs[4].plot(range(sim_time),load_ed_rd[6],'-y', label="ED6")
		axs[4].plot(range(sim_time),load_ed_rd[7],'-.b', label="ED7")
		axs[4].set(xlabel="simulation time (unit time)")
		axs[4].legend(loc="upper right")
		orch.legend(loc="upper left")
		plt.subplots_adjust(left=0.1,bottom=0.1,right=0.9,top=0.9,hspace=0.4)
		
		plt.show()	

		label=["IBOT-DAG","PETREL","LAVEA","RR","RD"]
		hat = ["x","|",".","+","/"]
		data = [average_service_time_ibot,average_service_time_petrel,average_service_time_lavea,average_service_time_rr,average_service_time_rd]
		plt.xticks(range(len(data)),label)
		plt.xlabel('Orchaestration scheme')
		plt.ylabel('Average service time (unit time)')
		for i in range(len(data)):
			plt.bar(i, data[i], hatch=hat[i]) 
		plt.show()

		ibot_av_pf=sum(ibot_av_pf)/num_arrivals
		petrel_av_pf=sum(petrel_av_pf)/num_arrivals
		lavea_av_pf=sum(lavea_av_pf)/num_arrivals
		rr_av_pf=sum(rr_av_pf)/num_arrivals
		rd_av_pf=sum(rd_av_pf)/num_arrivals


	#	fig1, axs = plt.subplots(1,sharex=True,figsize=(10,8))
	#	axs[0].plot(time_x,service_time_x, "*-", markevery=10,label="IBOT-PI")
	#	axs[0].title.set_text("Application instance service time")
	#	axs[0].set(ylabel="service time (unit time)")
	#	axs[0].set(xlabel="Application instance arrival time (unit time)")

		fig1, (pf,pf_tk) = plt.subplots(1,2,figsize=(10.5,5))
		pf.plot(pf_time,pf_ed_tk[0], '-.', markevery=40, label="ED0")
		pf.plot(pf_time,pf_ed_tk[1], '-.', markevery=40, label="ED1")
		pf.plot(pf_time,pf_ed_tk[2], '-.', markevery=40, label="ED2")
		pf.plot(pf_time,pf_ed_tk[3], '-.', markevery=40, label="ED3")
		pf.plot(pf_time,pf_ed_tk[4], '-.', markevery=40, label="ED4")
		pf.plot(pf_time,pf_ed_tk[5], '-.', markevery=40, label="ED5")
		pf.plot(pf_time,pf_ed_tk[6], '-.', markevery=40, label="ED6")
		pf.plot(pf_time,pf_ed_tk[7], '-.', markevery=40, label="ED7")
		pf.legend(loc="upper left")
		pf.set(ylabel="Probability of failure for EDs")
		pf.set(xlabel="Time passed (unit time)")
		pf.set_title('a')

		label=["IBOT-DAG","PETREL","LAVEA","RR","RD"]
		data = [1-ibot_av_pf,1-petrel_av_pf,1-lavea_av_pf,1-rr_av_pf,1-rd_av_pf]
		plt.xticks(range(len(data)),label)
		plt.xlabel('Orchaestration Scheme')
		plt.ylabel('Average probability of failure')
		plt.title('b')
		for i in range(len(data)):
			plt.bar(i, data[i], hatch=hat[i]) 
		plt.subplots_adjust(left=0.1,bottom=0.1,right=0.91,top=0.9,hspace=0.4)
		plt.show()


		label=["IBOT-DAG","PETREL","LAVEA","RR","RD"]
		mix=[10.4, 14.6, 15.89, 35.72, 34.34]
		ced=[8.96, 15.31, 16.1, 34.6, 31.88] 
		ped=[11.2, 15.2,  16.5, 34.13, 31.38]
		x_axis = np.arange(len(label))
		plt.bar(x_axis-0.3, mix, 0.25, label="mix", hatch="-")
		plt.bar(x_axis,     ced, 0.25, label="ced", hatch="x")
		plt.bar(x_axis+0.3, ped, 0.25, label="ped", hatch="|")
		plt.xticks(x_axis, label)
		plt.ylabel("Average service time(unit time)")
		plt.legend()
		plt.show()

		dum = [0.038,    0.069, 0.091, 0.118, 0.148]
		inv = [0.051,    0.086, 0.12,  0.168, 0.22]
		in_dum = [0.038, 0.078, 0.11,  0.156, 0.188]
		dum_in = [0.051, 0.07,  0.1,   0.135, 0.169]
		real = [0.038, 0.12,0.19,0.27,0.352]
		add=[0.038,0.147, 0.201, 0.274,0.336]
		x=[0 , 1, 2, 3, 4]
		plt.scatter(x,dum,color='r')
		plt.scatter(x,inv,color='b')
		plt.scatter(x,in_dum,color='g')
		plt.scatter(x,dum_in,color='m')
		plt.scatter(x,real,color="y")
		plt.scatter(x,add,color="c")
		
		z1 = np.polyfit(x,dum,1)
		z2 = np.polyfit(x,inv,1)
		z3 = np.polyfit(x,in_dum,1)
		z4 = np.polyfit(x,dum_in,1)
		z5 = np.polyfit(x,real,1)
		z6 = np.polyfit(x,add,1)
		p1 = np.poly1d(z1)
		p2 = np.poly1d(z2)
		p3 = np.poly1d(z3)
		p4 = np.poly1d(z4)
		p5 = np.poly1d(z5)
		p6 = np.poly1d(z6)

		plt.plot(x,p1(x),"r--",label="T(t1,k*t1)")
		plt.plot(x,p2(x),"b--",label="T(t2,k*t2)")
		plt.plot(x,p3(x),"g--",label="T(t1,k*t2)")
		plt.plot(x,p4(x),"m--",label="T(t2,k*t1)")
		plt.plot(x,p5(x),"y--",label="T_t2(j*t1,k*t2)")
		plt.plot(x,p6(x),"c--",label="T(t2,j*t1)+T(t2,k*t2)")
		plt.legend(loc="upper left")
		plt.ylabel("Average service time(s)")
		plt.xlabel("k, j (no of interfering tasks already running) ")
		plt.show()



	"""
		schedule_time_ibot = schedule_time_ibot/num_arrivals		
		schedule_time_petrel = schedule_time_petrel/num_arrivals
		schedule_time_lavea = schedule_time_lavea/num_arrivals
		schedule_time_rr = schedule_time_rr/num_arrivals
		schedule_time_rd = schedule_time_rd/num_arrivals
		if append_idx == 1 or append_idx == 11 or append_idx == 31 or append_idx == 61 or append_idx == 99:
			orch_time_ibot.append(schedule_time_ibot)
			orch_time_pet.append(schedule_time_petrel)
			orch_time_lav.append(schedule_time_lavea)
			orch_time_rr.append(schedule_time_rr)
			orch_time_rd.append(schedule_time_rd)
		append_idx+=1
	num_edge_inst = [1,11,31,61,100]
	fig2, axs2 = plt.subplots(1,sharex=True,figsize=(10,12))
	axs2.plot(num_edge_inst,orch_time_ibot,'<-' ,label="I-BOT")
	axs2.plot(num_edge_inst,orch_time_pet,'-*', label="PETREL")
	axs2.plot(num_edge_inst,orch_time_lav,'-X', label="LAVEA")
	axs2.plot(num_edge_inst,orch_time_rr,'-o', label="RR")
	axs2.plot(num_edge_inst,orch_time_rd,'>-', label="Random")
	axs2.set(xlabel="# of edge devices")
	axs2.set(ylabel="average scheduling time/ app instance (s)")
	axs2.legend(loc="upper left")
	plt.show()	
	"""
