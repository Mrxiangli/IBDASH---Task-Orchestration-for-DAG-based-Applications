import numpy as np
import pandas as pd
import time as timer
import pathlib
import argparse
import csv
import configparser
import logging
import os
import sys
import pprint
import math
import random
import json
import subprocess
import time as timer
import ast

from helpers import *
from helpers import plot as dagplot
from dispatcher import dispatch
from matplotlib import pyplot as plt
from matplotlib.animation import FuncAnimation
from sklearn import linear_model
from sklearn.preprocessing import PolynomialFeatures
from pathlib import Path
from threading import Thread
from queue import Queue
from icmplib import multiping
from multiprocessing import Process
import global_var 

pp = pprint.PrettyPrinter(indent=4)

def run_ibdash(task_time,num_edge,task_types,vert_stage,ED_m,ED_c,task_dict,dependency_dic,pf_ed,pf_ed_tk,task_file_dic,app_directory,inputfile_dic,socket_list,output_lookup,in_out_history,input_lookup):
	######### IBOT-PI ######### 
	print(in_out_history)
	pf_ibdash_av=[]
	service_time_ibdash=[]
	service_time_ibdash_norm=[]
	clock_time = np.arange(0,sim_time,1)
	# allocation history
	dispatcher_dic = {}

	#Dictionary that used for updated allocate tasks
	backtrack_dic={}
	for each_device in range(num_edge):
		backtrack_dic[each_device]={}
		for each_task in range(task_types):
			backtrack_dic[each_device][each_task]=[]

	# a dictionary that used to track the available models on each edge device	
	model_info=dict()
	for i in range(num_edge):
		model_info[i]=[]

	# A dictionary that used to track the available resource on each edge device, this should be read fro the profile data
	edge_info=dict()
	for i in range(num_edge) :
		edge_info[i]={"total": 10000, "available": 4000}

	# initialize the matrix to keep the all task info
	ED_tasks = [[[0 for i in range(len(clock_time))] for j in range(num_edge)] for k in range(task_types) ]

	k=0      	
	i=0
	instance_count = 0

	non_meta_files = {}			#tracking the non-meta-file on each device
	ntbd = 60

	meta_file_history_size={}	# tracking the metafile history size for transmission estimation

	#print(vert_stage)
	start_orch = timer.time()
	for time in clock_time:
		time = round(time,2)
		if time not in task_time:
			k+=1					# use k to track the unit time 
			timer.sleep(1)
		else:
			timer.sleep(1)
			i=0
			i_norm = 0
			instance_count += 1
			allocation={}
			ibot_success = 1					#probability of success
			tmp_pf_dic = {}						# temporary dictionary used to track probability of failure
			
			for stage in vert_stage:			# go through each stage in the dag
				longest_task_time=0
				longest_task_time_norm=0
				for each_task in vert_stage[stage]:			#go through each task in each stage
					fail_prev_queue = []
					t_pred=sys.maxsize
					exe_only=sys.maxsize
					ED_pred = 0
					task=int(each_task)
					ibot_pf_tk=1 # task pf tracker
					for j in range(num_edge):				#go through all the edge devices
						model_upload_t = 0
						data_trans_t = 0
						#print(f"edge device: {j}")
						w=ED_m[j][task*task_types:task*task_types+task_types]
						x=[]
						#print(f"k+i: {k+i}")	
						for idx in range(task_types):		# go through all task types: overall time complexity V * ed * num*task_type
							x.append(ED_tasks[idx][j][k+i])

						c=ED_c[j][task*task_types:task*task_types+task_types]
						#print(w)
						#print(x)
						if sum(np.array(x)>0) == 0:	# if no task is on the device
							predict_time = c[task]
						else:
							predict_time = int(np.dot(w,x)+np.dot((np.array(x)>0),c)) 		# this is merely the execution time
						#print(f"predict_time: {predict_time}")
						if predict_time < exe_only:
							exe_only = predict_time
						#print(f"exe_only {exe_only}")
						if task_dict[each_task][1][0]!="NULL":		# if a model is needed
							if task_dict[each_task][1] not in model_info[j]:
									model_upload_t = math.ceil(task_dict[each_task][1][1]/ntbd)			# ntbd need to be replaced with current network downloading speed
								#add the data transfer time
						
						#print(f" depend dic: {dependency_dic}")
						
						# obtain the input file for the current task 
						inputfile_current_task=[]
						for each_inputfile in input_lookup[str(task)]:
							if each_inputfile[1] == 0:
								inputfile_current_task.append(each_inputfile[0]+each_inputfile[2])
							else:
								inputfile_current_task.append(each_inputfile[0])

						# if the current task has no dependency, then no need to calculate data transmission time
						if dependency_dic[int(each_task)] != [None]:
							# if the current task has multiple dependency, then the one cuz the longest latency is the bottleneck
							for each_dep in dependency_dic[int(each_task)]:
								tmp_trans_time = 0
								if each_dep[1] == 1:		# indicate data dependency exists is its 1
									#check if the previous task is allocated on this potential device under testing (device j)
									if j in allocation[each_dep[0]]: 
										tmp_trans_time = 0
									else:
										# getting the transfer speed from the device the execute the previous task to the potential device j
										transfer_speed=global_var.ntwk_matrix[allocation[each_dep[0]][0]][j] 
										# tranfer speed = -1 indicates the previous tasks are allocated on the same device
										if transfer_speed == -1 or instance_count == 0:
											pass
										else:
											for each_input_file in inputfile_current_task:
												if global_var.in_out_history[int(each_task)]['input'][each_input_file]!= []:
													# using the previous file size: this can be changed accordingly later
													filesize = global_var.in_out_history[int(each_task)]['input'][each_input_file][-1]
													# print(f" filename: {filename}, size :{filesize}")
													tmp_trans_time = math.ceil(filesize/transfer_speed)
													if tmp_trans_time > data_trans_t:
														data_trans_t = tmp_trans_time
												else:
													# at the beginning of orchestration, need to warm up
													pass
						#sys.exit()
						predict_time = predict_time + model_upload_t + data_trans_t
						#print(f"total time: {predict_time}")
						if predict_time <= t_pred:		
							t_pred = predict_time
							ED_pred = j
						fail_prev_queue.append([j,predict_time])
					#print(f"t_pred:{t_pred}")
					fail_prev_queue=sorted(fail_prev_queue,key=lambda x: x[1])
					fail_prev_norm_queue=[]
					#print(fail_prev_queue)
					#print(num_rep)
					for serv_time in fail_prev_queue:
						norm_ele = [serv_time[0],serv_time[1]/fail_prev_queue[-1][1]] # this line has been changed!!! [num_rep-1] -> -1
						fail_prev_norm_queue.append(norm_ele)
					
					# This is new algorithm to prevent the repeated allocation the same performance device
					# pop out the fastest execution
					tmp_ED = []
					for each_element in fail_prev_queue:
						if each_element[1] == t_pred:
							tmp_ED.append(each_element[0])
					ED_pred=random.choice(tmp_ED)
					#ED_pred, t_pred=fail_prev_queue.pop(0)
					for each_element in fail_prev_norm_queue:
						if each_element[0] == ED_pred:
							t_pred_norm = each_element[1]
					#t_pred_norm = fail_prev_norm_queue.pop(0)[1]


					allocation[each_task]=[ED_pred]

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
						longest_task_time_norm=t_pred_norm

					ED_tasks, backtrack_dic=update_background_tasks(task_types,backtrack_dic,ED_pred,ED_m,ED_c,ED_tasks,k,i,task,exe_only, t_pred)

					# update the tasks running on each edge device	
					for j in range(k+i, k+i+t_pred):	
						ED_tasks[task][ED_pred][j]+=1

					parent_all_success = 1
					#Calculating the probability of current placement
					if dependency_dic[task] == [None]:
						#print("k+i:{}, k+i+t_pred:{}".format(k+i, k+i+t_pred))
						ProbF =  sum(pf_ed[ED_pred][task_time[0]:task_time[0]+i+t_pred])
						tmp_pf_dic[task] = ProbF
					else:
						#building a temporary dependency list
						current_task_parent=[]
						for depend_tracker in dependency_dic[task]:
							current_task_parent.append(depend_tracker[0])
						for each_parent in current_task_parent:
							parent_all_success = parent_all_success * (1-tmp_pf_dic[int(each_parent)])
						ProbF = 1-parent_all_success*(1-sum(pf_ed[ED_pred][task_time[0]:task_time[0]+i+t_pred]))
						tmp_pf_dic[task] = ProbF

					#weighed decision
					weighted_decision = weight*t_pred_norm+(1-weight)*ProbF
					replication = 0
					while ProbF > pF_thrs and replication < num_rep and fail_prev_queue:		# while the pf > pf_thre and replication < rep_num
						next_opt = fail_prev_queue.pop(0)
						# if the next popped is the chosen one already, pop the next
						while next_opt[0] == ED_pred:
							t_next_pred_norm = fail_prev_norm_queue.pop(0)[1]
							next_opt = fail_prev_queue.pop(0)
						t_next_pred_norm = fail_prev_norm_queue.pop(0)[1]
						t_next_pred = next_opt[1]
						t_next_ed = next_opt[0]
						new_ProbF = ProbF*(1-parent_all_success*(1-sum(pf_ed[t_next_ed][task_time[0]:task_time[0]+i+t_pred])))
						#print("new_ProbF: "+str(new_ProbF))
						#print("t_next_pred_norm: {}".format(t_next_pred_norm))
						if  weight*t_next_pred_norm+(1-weight)*new_ProbF < weighted_decision:
							#print("replicating...")
							ProbF=new_ProbF
							weighted_decision = weight*t_next_pred_norm+(1-weight)*ProbF
							replication+=1
							allocation[each_task].append(t_next_ed)
							if t_next_pred > longest_task_time:
								longest_task_time=t_next_pred
								longest_task_time_norm = t_next_pred_norm

							# update the pf for the tasks:
							tmp_pf_dic[task] = ProbF
							# update the task running on the replicated device
							for j in range(k+i, k+i+t_next_pred):
								ED_tasks[task][t_next_ed][j]+=1
							backtrack_dic[t_next_ed][task].append((k+i,k+i+t_next_pred)) ## newly added
				ibot_pf_tk = ProbF # probability of failure for a task
				ibot_success = ibot_success*(1-ibot_pf_tk)	#probability that the entire application is successsys.exit()
				i=i+longest_task_time	# tracking the end to end latency
				i_norm = i_norm + longest_task_time_norm
			if instance_count > 0 and instance_count % 10 == 0:
				p = Process(target=update_input_output_regression_history, args=(socket_list,instance_count,dependency_dic,dispatcher_dic,input_lookup,output_lookup,))
				p.start()
				#pass
			dispatcher_dic[instance_count]=allocation

			#allocation={'0': [0], '1': [1], '2': [0], '3': [1], '4': [0], '5': [1], '6': [0], '7': [1]}
			print(f"Task allocation for instance {instance_count} : {allocation}")
			print(f"Instance count {instance_count} start dispatching")
			get_times_stamp(instance_count)
			dispatch(app_directory,allocation,task_file_dic, instance_count, dependency_dic,inputfile_dic, socket_list,non_meta_files)
			#print(global_var.in_out_history)

			service_time_ibdash.append(i/1000)
			service_time_ibdash_norm.append(i_norm)
			k=k+1
			#print(allocation)
			pf_ibdash_av.append(tmp_pf_dic[task_types-1])
	end_orch = timer.time()
	#print(f"average orchestration time: {(end_orch-start_orch)/len(task_time)}")
	average_service_time_ibdash = sum(service_time_ibdash)/len(task_time)
	average_service_time_ibdash_norm = sum(service_time_ibdash_norm)/len(task_time)
	service_time_ibdash_x = []
	time_x = []
	load_ed = [0 for i in range(sim_time) for j in range(num_edge)]
	for each in range(0,sim_time):
		if each in task_time:
			service_time_ibdash_x.append(service_time_ibdash.pop(0))
			time_x.append(each/1000)

	for i in range(num_edge):
		for j in range(task_types):
			load_ed[i] = np.add(load_ed[i],ED_tasks[j][i])
	return time_x, average_service_time_ibdash, service_time_ibdash_x, pf_ibdash_av, load_ed, dispatcher_dic

def run_petrel(task_time,num_edge,task_types,vert_stage,ED_m,ED_c,task_dict,dependency_dic,pf_ed,pf_ed_tk,task_file_dic,app_directory,inputfile_dic,socket_list,output_lookup):

	########## Petrel ############
	# a dictionary that used to track the available models on each edge device	
	model_info=dict()
	for i in range(num_edge):
		model_info[i]=[]


	# A dictionary that used to track the available resource on each edge device, this should be read fro the profile data
	edge_info=dict()
	for i in range(num_edge) :
		edge_info[i]={"total": 10000, "available": 4000}

	clock_time = np.arange(0,sim_time,1)

	ED_tasks = [[[0 for i in range(len(clock_time))] for j in range(num_edge)] for k in range(task_types) ]
	schedule_time_petrel =0
	k=0
	i=0
	rp=0
	instance_count = 0
	service_time_petrel=[]
	non_meta_files = {}			#tracking the non-meta-file on each device
	for time in clock_time:
		time = round(time,2)
		if time not in task_time:
			k+=1					# use k to track the unit time 
			timer.sleep(1)
		else:
			timer.sleep(1)
			i=0
			start_time = timer.time()
			petrel_pf = 1
			instance_count += 1
			allocation={}
			tmp_pf_dic = {}						# temporary dictionary used to trakc probability of failure
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
						c=ED_c[j][task*task_types:task*task_types+task_types]
						predict_time = int(np.dot(w,x)+sum(c)) 		# this is merely the execution time
						if task_dict[each_task][1][0]!="NULL":	# if a model is needed
							if task_dict[each_task][1] not in model_info[j]:
									model_upload_t = math.ceil(task_dict[each_task][1][1]/ntbd)

						predict_time = predict_time + model_upload_t
						if predict_time < t_pred:		
							t_pred = predict_time
							ED_pred = j
					allocation[each_task]=[ED_pred]
					parent_all_success = 1
					#Calculating the probability of current placement
					if dependency_dic[task] == [None]:
						#print("k+i:{}, k+i+t_pred:{}".format(k+i, k+i+t_pred))
						ProbF =  sum(pf_ed[ED_pred][task_time[0]:task_time[0]+i+t_pred])
						tmp_pf_dic[task] = ProbF
						#print(tmp_pf_dic)
					else:
						#building a temporary dependency list
						current_task_parent=[]
						for depend_tracker in dependency_dic[task]:
							current_task_parent.append(depend_tracker[0])
						for each_parent in current_task_parent:
							parent_all_success = parent_all_success * (1-tmp_pf_dic[int(each_parent)])
						ProbF = 1-parent_all_success*(1-sum(pf_ed[ED_pred][task_time[0]:task_time[0]+i+t_pred]))
						tmp_pf_dic[task] = ProbF

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
			print(f"Task allocation for instance {instance_count} : {allocation}")
			print(f"Instance count {instance_count} start dispatching")
			get_times_stamp(instance_count)
			dispatch(app_directory,allocation,task_file_dic, instance_count, dependency_dic,inputfile_dic,socket_list,non_meta_files)
			service_time_petrel.append(i/1000)
			k=k+1
			pf_petrel_av.append(tmp_pf_dic[task_types-1])
	average_service_time_petrel = sum(service_time_petrel)/len(task_time)
	service_time_x_petrel = []
	time_x_petrel = []
	load_ed_petrel = [0 for i in range(sim_time) for j in range(num_edge)]
	for each in range(0,sim_time):
		if each in task_time:
			service_time_x_petrel.append(service_time_petrel.pop(0))
			time_x_petrel.append(each/1000)
		
	for i in range(num_edge):
		for j in range(task_types):
			load_ed_petrel[i] = np.add(load_ed_petrel[i],ED_tasks[j][i])

	return time_x_petrel, average_service_time_petrel, service_time_x_petrel, pf_petrel_av, load_ed_petrel

def run_lavea(task_time,num_edge,task_types,vert_stage,ED_m,ED_c,task_dict,dependency_dic,pf_ed,pf_ed_tk,task_file_dic,app_directory,inputfile_dic,socket_list,output_lookup):	
	# a dictionary that used to track the available models on each edge device	
	model_info=dict()
	for i in range(num_edge):
		model_info[i]=[]


	# A dictionary that used to track the available resource on each edge device, this should be read fro the profile data
	edge_info=dict()
	for i in range(num_edge) :
		edge_info[i]={"total": 10000, "available": 4000}

	clock_time = np.arange(0,sim_time,1)
	
	ED_tasks = [[[0 for i in range(len(clock_time))] for j in range(num_edge)] for k in range(task_types) ]

	k=0
	i=0
	rp=0
	instance_count = 0
	dispatcher_dic={}
	schedule_time_lavea = 0
	service_time_lavea=[]
	non_meta_files = {}			#tracking the non-meta-file on each device
	for time in clock_time:
		time = round(time,2)
		if time not in task_time:
			k+=1					# use k to track the unit time 
			timer.sleep(1)
		else:
			timer.sleep(1)
			i=0
			start_time = timer.time()
			lavea_pf = 1
			instance_count += 1
			allocation={}
			tmp_pf_dic = {}						# temporary dictionary used to trakc probability of failure
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
					allocation[each_task]=[ED_pred]
					model_upload_t = 0
					task=int(each_task)
					w=ED_m[ED_pred][task*task_types:task*task_types+task_types]
					x=[]		
					for idx in range(task_types):		# go through all task types   overall time complexity V * ed * num*task_type
						x.append(ED_tasks[idx][ED_pred][k+i])
					c=ED_c[ED_pred][task*task_types:task*task_types+task_types]
					predict_time = int(np.dot(w,x)+sum(c)) 		# this is merely the execution time
					#pp.pprint(task_dict)
					if task_dict[each_task][1][0]!="NULL":	# if a model is needed
						if task_dict[each_task][1] not in model_info[ED_pred]:
								model_upload_t = math.ceil(task_dict[each_task][1][1]/ntbd)
					predict_time = predict_time + model_upload_t
					t_pred = predict_time

					parent_all_success = 1
					#Calculating the probability of current placement
					if dependency_dic[task] == [None]:
						#print("k+i:{}, k+i+t_pred:{}".format(k+i, k+i+t_pred))
						ProbF =  sum(pf_ed[ED_pred][task_time[0]:task_time[0]+i+t_pred])
						tmp_pf_dic[task] = ProbF
						#print(tmp_pf_dic)
					else:
						#building a temporary dependency list
						current_task_parent=[]
						for depend_tracker in dependency_dic[task]:
							current_task_parent.append(depend_tracker[0])
						for each_parent in current_task_parent:
							parent_all_success = parent_all_success * (1-tmp_pf_dic[int(each_parent)])
						ProbF = 1-parent_all_success*(1-sum(pf_ed[ED_pred][task_time[0]:task_time[0]+i+t_pred]))
						tmp_pf_dic[task] = ProbF


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
			print(f"Task allocation for instance {instance_count} : {allocation}")
			print(f"Instance count {instance_count} start dispatching")
			get_times_stamp(instance_count)
			dispatch(app_directory,allocation,task_file_dic, instance_count, dependency_dic,inputfile_dic, socket_list,non_meta_files)
			service_time_lavea.append(i/1000)
			k=k+1
			pf_lavea_av.append(tmp_pf_dic[task_types-1])
	average_service_time_lavea = sum(service_time_lavea)/len(task_time)
	service_time_x_lavea = []
	time_x_lavea = []
	load_ed_lavea = [0 for i in range(sim_time) for j in range(num_edge)]
	for each in range(0,sim_time):
		if each in task_time:
			service_time_x_lavea.append(service_time_lavea.pop(0))
			time_x_lavea.append(each/1000)
			
	for i in range(num_edge):
		for j in range(task_types):
			load_ed_lavea[i] = np.add(load_ed_lavea[i],ED_tasks[j][i])
	return time_x_lavea, average_service_time_lavea, service_time_x_lavea, pf_lavea_av, load_ed_lavea


def run_round_robin(task_time,num_edge,task_types,vert_stage,ED_m,ED_c,task_dict,dependency_dic,pf_ed,pf_ed_tk,task_file_dic,app_directory,inputfile_dic,socket_list,output_lookup):
	########## Round Robin ############

	model_info=dict()
	for i in range(num_edge):
		model_info[i]=[]

	clock_time = np.arange(0,sim_time,1)
	schedule_time_rr = 0
	ED_tasks = [[[0 for i in range(len(clock_time))] for j in range(num_edge)] for k in range(task_types) ]
	non_meta_files = {}			#tracking the non-meta-file on each device
	k=0
	i=0
	rp=0
	rr_ed=1
	instance_count = 0
	dispatcher_dic={}
	service_time_rr=[]
	for time in clock_time:
		time = round(time,2)
		if time not in task_time:
			k+=1					# use k to track the unit time 
			timer.sleep(1)
		else:
			timer.sleep(1)
			i=0
			start_time = timer.time()
			rr_pf = 1
			instance_count += 1
			allocation={}
			tmp_pf_dic = {}						# temporary dictionary used to trakc probability of failure
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
					c=ED_c[ED_pred][task*task_types:task*task_types+task_types]
					predict_time = int(np.dot(w,x)+sum(c)) 		# this is merely the execution time
					#pp.pprint(task_dict)
					if task_dict[each_task][1][0]!="NULL":	# if a model is needed
						if task_dict[each_task][1] not in model_info[ED_pred]:
								model_upload_t = math.ceil(task_dict[each_task][1][1]/ntbd)

					predict_time = predict_time + model_upload_t
					t_pred = predict_time
					allocation[each_task]=[ED_pred]
					parent_all_success = 1
					#Calculating the probability of current placement
					if dependency_dic[task] == [None]:
						#print("k+i:{}, k+i+t_pred:{}".format(k+i, k+i+t_pred))
						ProbF =  sum(pf_ed[ED_pred][task_time[0]:task_time[0]+i+t_pred])
						tmp_pf_dic[task] = ProbF
						#print(tmp_pf_dic)
					else:
						#building a temporary dependency list
						current_task_parent=[]
						for depend_tracker in dependency_dic[task]:
							current_task_parent.append(depend_tracker[0])
						for each_parent in current_task_parent:
							parent_all_success = parent_all_success * (1-tmp_pf_dic[int(each_parent)])
						ProbF = 1-parent_all_success*(1-sum(pf_ed[ED_pred][task_time[0]:task_time[0]+i+t_pred]))
						tmp_pf_dic[task] = ProbF

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
			print(f"Task allocation for instance {instance_count} : {allocation}")
			print(f"Instance count {instance_count} start dispatching")
			get_times_stamp(instance_count)
			dispatch(app_directory,allocation,task_file_dic, instance_count, dependency_dic,inputfile_dic, socket_list,non_meta_files)
			service_time_rr.append(i/1000)
			k=k+1
			pf_rr_av.append(tmp_pf_dic[task_types-1])
	average_service_time_rr = sum(service_time_rr)/len(task_time)
	service_time_x_rr = []
	time_x_rr = []
	load_ed_rr = [0 for i in range(sim_time) for j in range(num_edge)]
	for each in range(0,sim_time):
		if each in task_time:
			service_time_x_rr.append(service_time_rr.pop(0))
			time_x_rr.append(each/1000)
			
	for i in range(num_edge):
		for j in range(task_types):
			load_ed_rr[i] = np.add(load_ed_rr[i],ED_tasks[j][i])
	return time_x_rr, average_service_time_rr, service_time_x_rr, pf_rr_av, load_ed_rr

def run_random(task_time,num_edge,task_types,vert_stage,ED_m,ED_c,task_dict,dependency_dic,pf_ed,pf_ed_tk,task_file_dic,app_directory,inputfile_dic,socket_list,output_lookup):
	########## Random ############

	model_info=dict()
	for i in range(num_edge):
		model_info[i]=[]

	clock_time = np.arange(0,sim_time,1)
	schedule_time_rd = 0
	ED_tasks = [[[0 for i in range(len(clock_time))] for j in range(num_edge)] for k in range(task_types) ]
	non_meta_files = {}			#tracking the non-meta-file on each device
	k=0
	i=0
	rp=0
	instance_count = 0
	dispatcher_dic={}
	service_time_rd=[]
	for time in clock_time:
		time = round(time,2)
		if time not in task_time:
			k+=1					# use k to track the unit time 
			timer.sleep(1)
		else:
			timer.sleep(1)
			i=0
			start_time = timer.time()
			rd_pf = 1
			instance_count += 1
			allocation={}
			tmp_pf_dic = {}						# temporary dictionary used to trakc probability of failure
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
					c=ED_c[ED_pred][task*task_types:task*task_types+task_types]
					predict_time = int(np.dot(w,x)+sum(c)) 		# this is merely the execution time
					#pp.pprint(task_dict)
					if task_dict[each_task][1][0]!="NULL":	# if a model is needed
						if task_dict[each_task][1] not in model_info[ED_pred]:
								model_upload_t = math.ceil(task_dict[each_task][1][1]/ntbd)

					predict_time = predict_time + model_upload_t
					t_pred = predict_time
					allocation[each_task]=[ED_pred]
					parent_all_success = 1
					#Calculating the probability of current placement
					if dependency_dic[task] == [None]:
						#print("k+i:{}, k+i+t_pred:{}".format(k+i, k+i+t_pred))
						ProbF =  sum(pf_ed[ED_pred][task_time[0]:task_time[0]+i+t_pred])
						tmp_pf_dic[task] = ProbF
						#print(tmp_pf_dic)
					else:
						#building a temporary dependency list
						current_task_parent=[]
						for depend_tracker in dependency_dic[task]:
							current_task_parent.append(depend_tracker[0])
						for each_parent in current_task_parent:
							parent_all_success = parent_all_success * (1-tmp_pf_dic[int(each_parent)])
						ProbF = 1-parent_all_success*(1-sum(pf_ed[ED_pred][task_time[0]:task_time[0]+i+t_pred]))
						tmp_pf_dic[task] = ProbF

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
			print(f"Task allocation for instance {instance_count} : {allocation}")
			print(f"Instance count {instance_count} start dispatching")
			get_times_stamp(instance_count)
			dispatch(app_directory,allocation,task_file_dic, instance_count, dependency_dic,inputfile_dic, socket_list,non_meta_files)
			service_time_rd.append(i/1000)
			k=k+1
			pf_rd_av.append(tmp_pf_dic[task_types-1])
	average_service_time_rd = sum(service_time_rd)/len(task_time)
	service_time_x_rd= []
	time_x_rd = []
	load_ed_rd = [0 for i in range(sim_time) for j in range(num_edge)]
	for each in range(0,sim_time):
		if each in task_time:
			service_time_x_rd.append(service_time_rd.pop(0))
			time_x_rd.append(each/1000)
			
	for i in range(num_edge):
		for j in range(task_types):
			load_ed_rd[i] = np.add(load_ed_rd[i],ED_tasks[j][i])
	return time_x_rd, average_service_time_rd, service_time_x_rd, pf_rd_av, load_ed_rd

def run_lats(task_time,num_edge,task_types,vert_stage,ED_m,ED_c,task_dict,dependency_dic,pf_ed,pf_ed_tk,task_file_dic,app_directory,inputfile_dic,socket_list, ed_cpu_regression,ed_latency_regression,output_lookup):
	# ########## LATs ############

	model_info=dict()
	for i in range(num_edge):
		model_info[i]=[]

	clock_time = np.arange(0,sim_time,1)
	schedule_time_lats = 0
	# task_ED_cpu = np.array(pd.read_excel(EDmc_path,engine="openpyxl",sheet_name="cpu",skiprows=0, nrows= num_edge))
	ED_tasks = [[[0 for i in range(len(clock_time))] for j in range(num_edge)] for k in range(task_types) ]
	# ED_usage = [[0 for i in range(len(clock_time))] for j in range(num_edge)]
	non_meta_files = {}			#tracking the non-meta-file on each device
	k=0
	i=0
	rp=0
	instance_count = 0
	poly = PolynomialFeatures(degree=3)
	service_time_lats=[]
	for time in clock_time:
		time = round(time,2)
		if time not in task_time:
			k+=1					# use k to track the unit time 
			timer.sleep(1)
		else:
			timer.sleep(1)
			i=0
			start_time = timer.time()
			lats_pf = 1
			instance_count += 1
			allocation={}
			tmp_pf_dic = {}						# temporary dictionary used to trakc probability of failure
			for stage in vert_stage:			# go through each stage in the dag
				longest_task_time=0
				#print("=============================================processing stage {}".format(stage))
				for each_task in vert_stage[stage]:			#go through each task in each stage
					t_pred=sys.maxsize
					ED_pred = 0
					task=int(each_task)
					#print("start scheduling task {}".format(each_task))
					for j in range(num_edge):
						#print("----testing on edge device {}".format(j))
						x=[]		
						for idx in range(task_types):		# go through all task types   overall time complexity V * ed * num*task_type
							x.append(ED_tasks[idx][j][k+i])
						predict_cpu_usage = ed_cpu_regression[j%8].predict(poly.fit_transform([x]))
						if j>8 and j<40:
							predict_cpu_usage = ed_cpu_regression[0].predict(poly.fit_transform([x]))
						if j>=40 and j<100:
							predict_cpu_usage = ed_cpu_regression[1].predict(poly.fit_transform([x]))
						#print(x)
						if sum(x) == 0:
							predict_cpu_usage = 0
						if abs(predict_cpu_usage) > 100:
							predict_cpu_usage = 100
						if abs(predict_cpu_usage) < 0:
							predict_cpu_usage = abs(predict_cpu_usage)
						if sum(x) > 0 and predict_cpu_usage < 10 :
							predict_cpu_usage = 50 
						if sum(x) > 0 and j%8 == 5 and predict_cpu_usage <10 :
							predict_cpu_usage = max(x)*20 
						if sum(x) > 0 and j%8 == 6 and predict_cpu_usage <10 :
							predict_cpu_usage = max(x)*15 
						if sum(x) > 0 and j%8 == 7 and predict_cpu_usage <10 :
							predict_cpu_usage = max(x)*20

						predict_time_log = ed_latency_regression[j%8][task](100-predict_cpu_usage)
						if j>8 and j<40:
							predict_time_log = ed_latency_regression[0][task](100-predict_cpu_usage)
						if j>=40 and j<100:
							predict_time_log = ed_latency_regression[1][task](100-predict_cpu_usage)
						#print(predict_cpu_usage)
						#print("predict_time_log {}".format(predict_time_log))
						predict_time = int(math.exp(predict_time_log))
						if predict_time < 0:
							predict_time = 100
						#print("predict cpu usage {}".format(predict_cpu_usage))
						#print("predict latency {}".format(predict_time))
						model_upload_t = 0
						if task_dict[each_task][1][0]!="NULL":	# if a model is needed
							if task_dict[each_task][1] not in model_info[ED_pred]:
									model_upload_t = math.ceil(task_dict[each_task][1][1]/ntbd)

						predict_time = predict_time + model_upload_t
						if predict_time < t_pred:
							t_pred = predict_time
							ED_pred = j
					allocation[each_task]=[ED_pred]
					parent_all_success = 1
					#Calculating the probability of current placement
					if dependency_dic[task] == [None]:
						#print("k+i:{}, k+i+t_pred:{}".format(k+i, k+i+t_pred))
						ProbF =  sum(pf_ed[ED_pred][task_time[0]:task_time[0]+i+t_pred])
						tmp_pf_dic[task] = ProbF
						#print(tmp_pf_dic)
					else:
						#building a temporary dependency list
						current_task_parent=[]
						for depend_tracker in dependency_dic[task]:
							current_task_parent.append(depend_tracker[0])
						for each_parent in current_task_parent:
							parent_all_success = parent_all_success * (1-tmp_pf_dic[int(each_parent)])
						ProbF = 1-parent_all_success*(1-sum(pf_ed[ED_pred][k+i:k+i+t_pred]))
						tmp_pf_dic[task] = ProbF

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
			schedule_time_lats = end_time - start_time
			#print("==========application instance at time {} is done with scheduling=======".format(time))
			get_times_stamp(instance_count)
			print(f"allocation for instance {instance_count}: {allocation}")
			dispatch(app_directory,allocation,task_file_dic, instance_count, dependency_dic,inputfile_dic, socket_list,non_meta_files)
			service_time_lats.append(i)
			#print(service_time_lats)
			k=k+1
			pf_lats_av.append(tmp_pf_dic[task_types-1])
	average_service_time_lats = sum(service_time_lats)/len(task_time)	
	service_time_x_lats= []
	time_x_lats = []
	load_ed_lats = [0 for i in range(sim_time) for j in range(num_edge)]
	for each in range(0,sim_time):
		if each in task_time:
			service_time_x_lats.append(service_time_lats.pop(0))
			time_x_lats.append(each)
			
	for i in range(num_edge):
		for j in range(task_types):
			load_ed_lats[i] = np.add(load_ed_lats[i],ED_tasks[j][i])
	return time_x_lats, average_service_time_lats, service_time_x_lats, pf_lats_av, load_ed_lats




if __name__ =='__main__':

	# Instantiate the parser
	parser = argparse.ArgumentParser()
	parser.add_argument('--app', type=str, nargs="?", const="matrix_app", default="matrix_app",help='app: one of matrix_app, video_app, mapreduce, lightgbm')
	parser.add_argument('--mc', type=str, nargs="?", const="ED_mc_mt.xlsx", default="ED_mc_mt.xlsx",help='the .xlsx file that saves the m,c value pairs')
	parser.add_argument('--pf', type=float, nargs="?", const=0.25, default=0.25,help='probability of falure threshold beta')
	parser.add_argument('--rd', type=int, nargs="?", const=3, default=3,help='replication degree gamma')
	parser.add_argument('--jp', type=float, nargs="?", const=0.5, default=0.5,help='joint optimization parameter alpha')
	parser.add_argument('--sch', type=str, nargs="?", const="ibdash", default="ibdash",help='joint optimization parameter alpha')
	args = parser.parse_args()

	global_var.initialize()

	profile_data_path = os.path.join(os.getcwd(),"profile_data/")
	app_path = os.path.join(profile_data_path,args.app)
	app_json = os.path.join(app_path,'app_config.json')
	connection_q = Queue()

	
	# Opening JSON file that contains the application dag
	f = open(app_json) 
	app_data, original_dag, linear_dags, vertices, edge_adj = dag_linearization(f)
	task_dict=task_info(vertices)
	dagplot(original_dag)
	vert_dict, vert_stage = app_stage(edge_adj)
	task_types = len(task_dict)-1

	dependency_dic=dependency_dic(app_data,task_dict)
	depend_lookup=dependency_lookup(app_data)
	inputfile_dic=inputfile_dic(app_data)
	input_lookup=inputfile_lookup(app_data)
	output_lookup=output_lookup(app_data)

	task_file_dic={} #use this dictionary to track the file need to be used in each task
	for task in app_data['Application']['Vertices']:
		task_file_dic[task['name']]=task['file'][0]

	global_var.in_out_history=creat_input_output_regression_history(app_path,dependency_dic,input_lookup,output_lookup)


	EDmc_file=os.path.join(app_path,args.mc) # this file has the (m,c) value pairs and should be updated dynamically later on
	
	# The following parameters can be used to tune the simulation
	random.seed(0)
	ntbd = 600							#network bandwidth
	app_inst_time = 250				#the period of time that application instances might arrive
	sim_time = 20000					#simulation period
	num_arrivals = 100					#number of application instances arrived during app_ins_time	
	pF_thrs = args.pf					#probability of failure threshold
	num_rep = args.rd					#maximum number of replication allowed
	weight = args.jp 					#use this to control the joint optimization parameter alpha
	num_edge_max = 5					#number of edge devices in DAG
	global_var.transmission_err_prov = 1

	access_dict={}
	access_dict[0]="128.46.74.171" #nx1
	access_dict[1]="128.46.74.172" #nx2
	access_dict[2]="128.46.74.173" #nx3
	access_dict[3]="128.46.74.95"  #agx
	access_dict[4]="128.46.32.175" #ashraf server
	access_dict[5]="128.46.73.218" #orchestrator
	
	global_var.device_list=[]
	global_var.socket_list = []
	global_var.IDENTIFIER = num_edge_max
	global_var.ntwk_matrix=create_ntwk_matrix(num_edge_max+1)

	for each in access_dict.keys():
		global_var.device_list.append(access_dict[each])

	# creat connection socket for each edge device
	for i in range(num_edge_max):
		s = socket_connections(access_dict[i],5001)
		global_var.socket_list.append(s)

	# creat listening thread for each device
	for i in range(num_edge_max):
		Thread(target = connection_listening_thread, args=(global_var.socket_list[i],access_dict[i])).start() # for each socket connection in connection queue, creat a listenning thread and listen to command or receive files


	dependency_file,task_file,dependency_lookup,input_lp,output_lp,edge_list=loading_input_files(dependency_dic,depend_lookup,input_lookup,output_lookup,task_file_dic,access_dict)

	# send identifier to each device, every device aware the presence of other devices
	for idx,each in enumerate(global_var.socket_list):
		send_label(global_var.socket_list[idx],idx)
		send_files(global_var.socket_list[idx],edge_list)

	# send the application related files to each device, this only nee to be done one time
	for idx,each in enumerate(global_var.socket_list):
		send_files(global_var.socket_list[idx],dependency_file)
		send_files(global_var.socket_list[idx],task_file)
		send_files(global_var.socket_list[idx],dependency_lookup)
		send_files(global_var.socket_list[idx],input_lp)
		send_files(global_var.socket_list[idx],output_lp)

	# start the network speed test
	if args.sch == "ibdash":
		periodic_network_test()

	#generate the random task arrival time 
	task_time = np.array(sorted(random.sample(range(1,app_inst_time),num_arrivals)))
	
	# following used to control the simulation cycle
	"""
	for m in range(1,10):
		new_cycle_arrival = np.array(sorted(random.sample(range(m*15000,m*15000+app_inst_time),num_arrivals)))
		task_time=np.concatenate((task_time,sorted(new_cycle_arrival)))
	"""

	#building the cpu regression model and latency regression model for all edge devices
	#===================== This piece of code is used for LaTS simulation, not necessary in the upcoming version
	if args.sch == "lats":
		ed_cpu_regression = cpu_regression_setup(task_types,num_edge_max,app_path)
		ed_latency_regression = latency_regression_setup(task_types,num_edge_max,EDmc_file)

	
	pf_petrel_av=[]
	pf_lavea_av=[]
	pf_rr_av=[]
	pf_rd_av=[]
	pf_lats_av=[]

	app_directory = os.path.join(profile_data_path,args.app)


	# This outer loop can be used to check for the orchestration overhead with setting the timer at correct place
	for edge_index in range(num_edge_max-1,num_edge_max):

		num_edge = edge_index+1

		ED_m = np.array(pd.read_excel(EDmc_file,engine="openpyxl",sheet_name="edm",skiprows=0, nrows= num_edge))
		ED_c = np.array(pd.read_excel(EDmc_file,engine="openpyxl",sheet_name="edc",skiprows=0, nrows= num_edge))

		#probabily of failure for each edge device (used expotential distribution for simulation)
		#lam2=[0.000000015, 0.00000011, 0.000000015, 0.000000024, 0.00000009, 0.000000032, 0.00000031, 0.00000001,0.0000015,0.0000015]   	#mix
		lam2 = [0,0,0,0,0,0,0,0,]
		#lam2=[0.00015, 0.00011, 0.00015, 0.00024, 0.0009, 0.000032, 0.0001, 0.0009]   									#PED
		#lam2=[0.000015, 0.000011, 0.000015, 0.000011, 0.000018, 0.000012, 0.00001, 0.00002]   							#CED

		# use the follwing loop to update the failure rate for each devive
		for i in range(num_edge):
			lam2 = np.concatenate((lam2,lam2))
		


		pf_ed = [0 for i in range(sim_time) for j in range(num_edge)]
		pf_ed_tk = [0 for i in range(sim_time) for j in range(num_edge)]
		pf_time = np.arange(0, sim_time, 1)

		# probability of failure
		for i in range(num_edge):
			pf_ed[i]=lam2[i]*np.exp(-1*lam2[i]*pf_time)
			pf_ed_tk[i]= 1-np.exp(-1*lam2[i]*pf_time)				

		pf_time = np.arange(0, sim_time/1000, 0.001)

			# a dictionary that used to track the available models on each edge device	
		model_info=dict()
		for i in range(num_edge):
			model_info[i]=[]

		# A dictionary that used to track the available resource on each edge device, this should be read fro the profile data
		edge_info=dict()
		for i in range(num_edge) :
			edge_info[i]={"total": 10000, "available": 4000}
		if args.sch == "ibdash":
			time_x, average_service_time_ibdash, service_time_ibdash_x, pf_ibdash_av,load_ed,dispatcher_dic=run_ibdash(task_time,num_edge,task_types,vert_stage,ED_m,ED_c,task_dict,dependency_dic,pf_ed,pf_ed_tk, task_file_dic,app_directory,inputfile_dic, global_var.socket_list,output_lookup,global_var.in_out_history,input_lookup)
		if args.sch == "petrel":
			time_x_petrel, average_service_time_petrel, service_time_x_petrel, pf_petrel_av,load_ed_petrel=run_petrel(task_time,num_edge,task_types,vert_stage,ED_m,ED_c,task_dict,dependency_dic,pf_ed,pf_ed_tk, task_file_dic,app_directory,inputfile_dic, global_var.socket_list,output_lookup)
		if args.sch == "lavea":
			time_x_lavea, average_service_time_lavea, service_time_x_lavea, pf_lavea_av,load_ed_lavea=run_lavea(task_time,num_edge,task_types,vert_stage,ED_m,ED_c,task_dict,dependency_dic,pf_ed,pf_ed_tk, task_file_dic,app_directory,inputfile_dic, global_var.socket_list,output_lookup)
		if args.sch == "rr":
			time_x_rr, average_service_time_rr, service_time_x_rr, pf_rr_av,load_ed_rr=run_round_robin(task_time,num_edge,task_types,vert_stage,ED_m,ED_c,task_dict,dependency_dic,pf_ed,pf_ed_tk, task_file_dic,app_directory,inputfile_dic, global_var.socket_list,output_lookup)
		if args.sch == "rd":
			time_x_rd, average_service_time_rd, service_time_x_rd, pf_rd_av,load_ed_rd=run_random(task_time,num_edge,task_types,vert_stage,ED_m,ED_c,task_dict,dependency_dic,pf_ed,pf_ed_tk, task_file_dic,app_directory,inputfile_dic, global_var.socket_list,output_lookup)
		if args.sch == "lats":
			time_x_lats, average_service_time_lats, service_time_x_lats, pf_lats_av,load_ed_lats=run_lats(task_time,num_edge,task_types,vert_stage,ED_m,ED_c,task_dict,dependency_dic,pf_ed,pf_ed_tk, task_file_dic,app_directory,inputfile_dic, global_var.socket_list, ed_cpu_regression,ed_latency_regression,output_lookup)

		#print(f"service time ibdash: {average_service_time_ibdash}")
		#print(f"service time petrel: {average_service_time_petrel}")
		#print(f"service time lavea: {average_service_time_lavea}")
		#print(f"service time rr: {average_service_time_rr}")
		#print(f"service time rd: {average_service_time_rd}")
		#print(f"service time lats: {average_service_time_lats}")