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

from helpers import insert_edge_device, insert_task, app_stage, task_info, cpu_regression_setup,latency_regression_setup,dag_linearization,dependency_dic, inputfile_dic, dependency_lookup, inputfile_lookup, output_lookup, get_times_stamp, ping_test
from helpers import plot as dagplot
from dispatcher import dispatch, createSSHClient
from matplotlib import pyplot as plt
from matplotlib.animation import FuncAnimation
from sklearn import linear_model
from sklearn.preprocessing import PolynomialFeatures
from pathlib import Path

pp = pprint.PrettyPrinter(indent=4)


def run_ibdash(task_time,num_edge,task_types,vert_stage,ED_m,ED_c,task_dict,dependency_dic,pf_ed,pf_ed_tk,task_file_dic,edge_list_scp,edgelist_ssh,app_directory,inputfile_dic):
	######### IBOT-PI ######### 
	
	pf_ibdash_av=[]
	service_time_ibdash=[]
	service_time_ibdash_norm=[]
	clock_time = np.arange(0,sim_time,1)

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
	dispatcher_dic={}

	for time in clock_time:
		time = round(time,2)
		if time not in task_time:
			k+=1					# use k to track the unit time 
		else:
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
					ED_pred = 0
					ibot_pf_tk=1 # task pf tracker
					for j in range(num_edge):				#go through all the edge devices
						model_upload_t = 0
						data_trans_t = 0
						task=int(each_task)
						w=ED_m[j][task*task_types:task*task_types+task_types]
						x=[]		
						for idx in range(task_types):		# go through all task types   overall time complexity V * ed * num*task_type
							x.append(ED_tasks[idx][j][k+i])
						c=ED_c[j][task*task_types:task*task_types+task_types]
						predict_time = int(np.dot(w,x)+sum(c)) 		# this is merely the execution time
						if task_dict[each_task][1][0]!="NULL":		# if a model is needed
							if task_dict[each_task][1] not in model_info[j]:
									model_upload_t = math.ceil(task_dict[each_task][1][1]/ntbd)
								#add the data transfer time
						if dependency_dic[int(each_task)] != [None]:
							for each_dep in dependency_dic[int(each_task)]:
								if each_dep[1] == 1:
									# obtain the result size, using a fixed size for testing
									data_trans_tmp = math.ceil(1200/ntbd)
									if	data_trans_tmp > data_trans_t:
										data_trans_t = data_trans_tmp

						predict_time = predict_time + model_upload_t + data_trans_t
						if predict_time < t_pred:		
							t_pred = predict_time
							ED_pred = j
						fail_prev_queue.append([j,predict_time])
					fail_prev_queue=sorted(fail_prev_queue,key=lambda x: x[1])
					fail_prev_norm_queue=[]
					for serv_time in fail_prev_queue:
						norm_ele = [serv_time[0],serv_time[1]/fail_prev_queue[num_rep-1][1]]
						fail_prev_norm_queue.append(norm_ele)

					ED_pred, t_pred=fail_prev_queue.pop(0)
					t_pred_norm = fail_prev_norm_queue.pop(0)[1]
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

					#print("PF for task {} at initial schedue on edge {}: {}. The latency is t_pred: {}".format(task,ED_pred,ProbF,t_pred))
					#weighed decision
					weighted_decision = weight*t_pred_norm+(1-weight)*ProbF
					replication = 0
					while ProbF > pF_thrs and replication < num_rep and fail_prev_queue:		# while the pf > pf_thre and replication < rep_num
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
				ibot_pf_tk = ProbF # probability of failure for a task
				ibot_success = ibot_success*(1-ibot_pf_tk)	#probability that the entire application is successsys.exit()
				i=i+longest_task_time	# tracking the end to end latency
				i_norm = i_norm + longest_task_time_norm

			dispatcher_dic[instance_count]=allocation
			allocation={"0": [0], "1": [1,2], "2": [0]}
			print(allocation)
			print("instance cout start :{}".format(instance_count))
			get_times_stamp(instance_count)
			dispatch(app_directory,allocation,edge_list_scp,edge_list_ssh,task_file_dic, instance_count, dependency_dic,inputfile_dic)
			service_time_ibdash.append(i/1000)
			service_time_ibdash_norm.append(i_norm)
			k=k+1
			#print(allocation)
			pf_ibdash_av.append(tmp_pf_dic[task_types-1])
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

def run_petrel(task_time,num_edge,task_types,vert_stage,ED_m,ED_c,task_dict,dependency_dic,pf_ed,pf_ed_tk,task_file_dic,edge_list_scp,edgelist_ssh,app_directory,inputfile_dic):

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
	for time in clock_time:
		time = round(time,2)
		if time not in task_time:
			k+=1					# use k to track the unit time 
		else:
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
			get_times_stamp(instance_count)
			dispatch(app_directory,allocation,edge_list_scp,edge_list_ssh,task_file_dic, instance_count, dependency_dic,inputfile_dic)
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

def run_lavea(task_time,num_edge,task_types,vert_stage,ED_m,ED_c,task_dict,dependency_dic,pf_ed,pf_ed_tk,task_file_dic,edge_list_scp,edgelist_ssh,app_directory,inputfile_dic):	
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
	for time in clock_time:
		time = round(time,2)
		if time not in task_time:
			k+=1					# use k to track the unit time 
		else:
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
			get_times_stamp(instance_count)
			dispatch(app_directory,allocation,edge_list_scp,edge_list_ssh,task_file_dic, instance_count, dependency_dic,inputfile_dic)
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


def run_round_robin(task_time,num_edge,task_types,vert_stage,ED_m,ED_c,task_dict,dependency_dic,pf_ed,pf_ed_tk,task_file_dic,edge_list_scp,edgelist_ssh,app_directory,inputfile_dic):
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
	instance_count = 0
	dispatcher_dic={}
	service_time_rr=[]
	for time in clock_time:
		time = round(time,2)
		if time not in task_time:
			k+=1					# use k to track the unit time 
		else:
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
			get_times_stamp(instance_count)
			dispatch(app_directory,allocation,edge_list_scp,edge_list_ssh,task_file_dic, instance_count, dependency_dic,inputfile_dic)
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

def run_random(task_time,num_edge,task_types,vert_stage,ED_m,ED_c,task_dict,dependency_dic,pf_ed,pf_ed_tk,task_file_dic,edge_list_scp,edgelist_ssh,app_directory,inputfile_dic):
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
	instance_count = 0
	dispatcher_dic={}
	service_time_rd=[]
	for time in clock_time:
		time = round(time,2)
		if time not in task_time:
			k+=1					# use k to track the unit time 
		else:
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
			get_times_stamp(instance_count)
			dispatch(app_directory,allocation,edge_list_scp,edge_list_ssh,task_file_dic, instance_count, dependency_dic,inputfile_dic)
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

def run_lats(task_time,num_edge,task_types,vert_stage,ED_m,ED_c,task_dict,dependency_dic,pf_ed,pf_ed_tk,task_file_dic,edge_list_scp,edgelist_ssh,app_directory,inputfile_dic,ed_cpu_regression,ed_latency_regression):
	# ########## LATs ############

	model_info=dict()
	for i in range(num_edge):
		model_info[i]=[]

	clock_time = np.arange(0,sim_time,1)
	schedule_time_lats = 0
	# task_ED_cpu = np.array(pd.read_excel(EDmc_path,engine="openpyxl",sheet_name="cpu",skiprows=0, nrows= num_edge))
	ED_tasks = [[[0 for i in range(len(clock_time))] for j in range(num_edge)] for k in range(task_types) ]
	# ED_usage = [[0 for i in range(len(clock_time))] for j in range(num_edge)]

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
		else:
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
			dispatch(app_directory,allocation,edge_list_scp,edge_list_ssh,task_file_dic, instance_count, dependency_dic,inputfile_dic)
			service_time_lats.append(i/1000)
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
			time_x_lats.append(each/1000)
			
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
	args = parser.parse_args()

	profile_data_path = os.path.join(os.getcwd(),"profile_data/")
	app_path = os.path.join(profile_data_path,args.app)
	app_json = os.path.join(app_path,'app_config.json')
	

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

	EDmc_file=os.path.join(app_path,args.mc) # this file has the (m,c) value pairs and should be updated dynamically later on
	# The following parameters can be used to tune the simulation
	random.seed(0)
	ntbd = 600						#network bandwidth
	app_inst_time = 150				#the period of time that application instances might arrive
	sim_time = 200000				#simulation period
	num_arrivals = 1				#number of application instances arrived during app_ins_time	
	pF_thrs = args.pf					#probability of failure threshold
	num_rep = args.rd					#maximum number of replication allowed
	weight = args.jp 					#use this to control the joint optimization parameter alpha
	num_edge_max = 3					#number of edge devices in DAG

	edge_list_scp=[]
	edge_list_ssh=[]
	unavailable_edge = []
	access_dict={}
	access_dict[0]="ec2-107-23-36-58.compute-1.amazonaws.com"
	access_dict[1]="ec2-3-239-208-120.compute-1.amazonaws.com"
	access_dict[2]="ec2-3-234-212-152.compute-1.amazonaws.com"
	access_dict[3]="128.46.73.218"

	for i in range(num_edge_max):
		availibility = ping_test(access_dict[i])
		if availibility == -1:
			access_dict.pop(i)
			unavailable_edge.append(i)

	sys.exit()

	dependency_file = "dependency_file.json"
	with open(dependency_file,'w') as depend_file:
		depend_file.write(json.dumps(dependency_dic))
	depend_file.close()

	task_file = "task_file.json"
	with open(task_file,'w') as tk_file:
		tk_file.write(json.dumps(task_file_dic))
	tk_file.close()

	dependency_lookup = "depend_lookup.json"
	with open(dependency_lookup,'w') as lk_file:
		lk_file.write(json.dumps(depend_lookup))
	lk_file.close()

	input_lp = "input_lookup.json"
	with open(input_lp,'w') as lp_file:
		lp_file.write(json.dumps(input_lookup))
	lp_file.close()

	output_lp = "output_lookup.json"
	with open(output_lp,'w') as op_file:
		op_file.write(json.dumps(output_lookup))
	op_file.close()

	for i in range(4):
		if i < 3:
			client_scp, client_ssh = createSSHClient(access_dict[i],"IBDASH_V2.pem")
			client_ssh.exec_command("source ~/.bashrc")
		else:
			client_scp, client_ssh = createSSHClient(access_dict[i],"id_rsa.pub" )
		edge_list_scp.append(client_scp)
		edge_list_ssh.append(client_ssh)

	for each in edge_list_scp:
		each.put(dependency_file)
		each.put(task_file)
		each.put(dependency_lookup)
		each.put(input_lp)
		each.put(output_lp)
		each.put("governer.py")
		


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
		lam2=[0.000000015, 0.0000011, 0.000000015, 0.000024, 0.000009, 0.0000032, 0.000031, 0.0000001,0.0000015,0.0000015]   	#mix
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

		time_x, average_service_time_ibdash, service_time_ibdash_x, pf_ibdash_av,load_ed,dispatcher_dic=run_ibdash(task_time,num_edge,task_types,vert_stage,ED_m,ED_c,task_dict,dependency_dic,pf_ed,pf_ed_tk, task_file_dic,edge_list_scp,edge_list_ssh,app_directory,inputfile_dic)
		#time_x_petrel, average_service_time_petrel, service_time_x_petrel, pf_petrel_av,load_ed_petrel=run_petrel(task_time,num_edge,task_types,vert_stage,ED_m,ED_c,task_dict,dependency_dic,pf_ed,pf_ed_tk,task_file_dic,edge_list_scp,edge_list_ssh,app_directory,inputfile_dic)
		#time_x_lavea, average_service_time_lavea, service_time_x_lavea, pf_lavea_av,load_ed_lavea=run_lavea(task_time,num_edge,task_types,vert_stage,ED_m,ED_c,task_dict,dependency_dic,pf_ed,pf_ed_tk,task_file_dic,edge_list_scp,edge_list_ssh,app_directory,inputfile_dic)
		#time_x_rr, average_service_time_rr, service_time_x_rr, pf_rr_av,load_ed_rr=run_round_robin(task_time,num_edge,task_types,vert_stage,ED_m,ED_c,task_dict,dependency_dic,pf_ed,pf_ed_tk,task_file_dic,edge_list_scp,edge_list_ssh,app_directory,inputfile_dic)
		#time_x_rd, average_service_time_rd, service_time_x_rd, pf_rd_av,load_ed_rd=run_random(task_time,num_edge,task_types,vert_stage,ED_m,ED_c,task_dict,dependency_dic,pf_ed,pf_ed_tk,task_file_dic,edge_list_scp,edge_list_ssh,app_directory,inputfile_dic)
		#time_x_lats, average_service_time_lats, service_time_x_lats, pf_lats_av,load_ed_lats=run_lats(task_time,num_edge,task_types,vert_stage,ED_m,ED_c,task_dict,dependency_dic,pf_ed,pf_ed_tk,task_file_dic,edge_list_scp,edge_list_ssh,app_directory,inputfile_dic,ed_cpu_regression,ed_latency_regression)

"""
		fig2, orch = plt.subplots(3,2,sharex=True)
		fig2.tight_layout()
		orch[0][0].plot(time_x,service_time_ibdash_x,"b-",markevery=10,label="service time")
		orch[0][1].plot(time_x_petrel,service_time_x_petrel, "b-", markevery=10,label="service time")
		orch[1][0].plot(time_x_lavea,service_time_x_lavea,"b-", markevery=10,label="service time")
		orch[1][1].plot(time_x_rr,service_time_x_rr,"b-", markevery=10,label="service time")
		orch[2][0].plot(time_x_rd,service_time_x_rd,"b-", markevery=10,label="service time")
		orch[2][1].plot(time_x_lats,service_time_x_lats,"b-", markevery=10,label="service time")

		orch[0][0].set_ylabel("service time (s)",fontsize=13)
		orch[1][0].set_ylabel("service time (s)",fontsize=13)
		orch[2][0].set_ylabel("service time (s)",fontsize=13)
		orch[2][0].set_xlabel("Application instance arrival time (s)",fontsize=13)
		orch[2][1].set_xlabel("Application instance arrival time (s)",fontsize=13)

		orch[0][0].set_title('IBDASH')
		orch[0][1].set_title('PETREL')
		orch[1][0].set_title('LAVEA')
		orch[1][1].set_title('RR')
		orch[2][0].set_title('RD')
		orch[2][1].set_title('LaTS')

		orch[0][0].legend(loc='upper left')
		orch[0][1].legend(loc='upper left')
		orch[1][0].legend(loc='upper left')
		orch[1][1].legend(loc='upper left')
		orch[2][0].legend(loc='upper left')
		orch[2][1].legend(loc='upper left')

		fig1, axs = plt.subplots(3,2,sharex=True)
		fig1.tight_layout()
		axs[0][0].plot(np.arange(0,sim_time/1000,0.001),load_ed[0],'-b' ,label="ED0")	
		axs[0][0].plot(np.arange(0,sim_time/1000,0.001),load_ed[1],'-r', label="ED1")
		axs[0][0].plot(np.arange(0,sim_time/1000,0.001),load_ed[2],'-g', label="ED2")
		axs[0][0].plot(np.arange(0,sim_time/1000,0.001),load_ed[3],'-c' , label="ED3")
		axs[0][0].plot(np.arange(0,sim_time/1000,0.001),load_ed[4],'-m', label="ED4")
		axs[0][0].plot(np.arange(0,sim_time/1000,0.001),load_ed[5],'-k', label="ED5")
		axs[0][0].plot(np.arange(0,sim_time/1000,0.001),load_ed[6],'-y' , label="ED6")
		axs[0][0].plot(np.arange(0,sim_time/1000,0.001),load_ed[7],'-.b', label="ED7")
		
		axs[0][0].legend(loc="upper right")
		axs[0][0].set_ylabel("# tasks",fontsize=16)
		axs[0][0].set_title("IBDASH",fontsize=14)

		axs[0][1].plot(np.arange(0,sim_time/1000,0.001),load_ed_petrel[0],'-b' ,label="ED0")
		axs[0][1].plot(np.arange(0,sim_time/1000,0.001),load_ed_petrel[1],'-r', label="ED1")
		axs[0][1].plot(np.arange(0,sim_time/1000,0.001),load_ed_petrel[2],'-g', label="ED2")
		axs[0][1].plot(np.arange(0,sim_time/1000,0.001),load_ed_petrel[3],'-c' , label="ED3")
		axs[0][1].plot(np.arange(0,sim_time/1000,0.001),load_ed_petrel[4],'-m', label="ED4")
		axs[0][1].plot(np.arange(0,sim_time/1000,0.001),load_ed_petrel[5],'-k', label="ED5")
		axs[0][1].plot(np.arange(0,sim_time/1000,0.001),load_ed_petrel[6],'-y', label="ED6")
		axs[0][1].plot(np.arange(0,sim_time/1000,0.001),load_ed_petrel[7],'-.b', label="ED7")
		axs[0][1].legend(loc="upper right")
		axs[0][1].set_ylabel("# tasks", fontsize=14)
		axs[0][1].set_title("PETREL",fontsize=16)
		
		
		axs[1][0].plot(np.arange(0,sim_time/1000,0.001),load_ed_lavea[0],'-b' ,label="ED0")
		axs[1][0].plot(np.arange(0,sim_time/1000,0.001),load_ed_lavea[1],'-r', label="ED1")
		axs[1][0].plot(np.arange(0,sim_time/1000,0.001),load_ed_lavea[2],'-g', label="ED2")
		axs[1][0].plot(np.arange(0,sim_time/1000,0.001),load_ed_lavea[3],'-c' , label="ED3")
		axs[1][0].plot(np.arange(0,sim_time/1000,0.001),load_ed_lavea[4],'-m', label="ED4")
		axs[1][0].plot(np.arange(0,sim_time/1000,0.001),load_ed_lavea[5],'-k', label="ED5")
		axs[1][0].plot(np.arange(0,sim_time/1000,0.001),load_ed_lavea[6],'-y', label="ED5")
		axs[1][0].plot(np.arange(0,sim_time/1000,0.001),load_ed_lavea[7],'-.b', label="ED6")
		axs[1][0].legend(loc="upper right")
		axs[1][0].set_ylabel("# tasks", fontsize=14)
		axs[1][0].set_title("LAVEA",fontsize=16)
			
		
		axs[1][1].plot(np.arange(0,sim_time/1000,0.001),load_ed_rr[0],'-b' ,label="ED0")
		axs[1][1].plot(np.arange(0,sim_time/1000,0.001),load_ed_rr[1],'-r', label="ED1")
		axs[1][1].plot(np.arange(0,sim_time/1000,0.001),load_ed_rr[2],'-g', label="ED2")
		axs[1][1].plot(np.arange(0,sim_time/1000,0.001),load_ed_rr[3],'-c' , label="ED3")
		axs[1][1].plot(np.arange(0,sim_time/1000,0.001),load_ed_rr[4],'-m', label="ED4")
		axs[1][1].plot(np.arange(0,sim_time/1000,0.001),load_ed_rr[5],'-k', label="ED5")
		axs[1][1].plot(np.arange(0,sim_time/1000,0.001),load_ed_rr[6],'-y', label="ED5")
		axs[1][1].plot(np.arange(0,sim_time/1000,0.001),load_ed_rr[7],'-.b', label="ED6")
		axs[1][1].legend(loc="upper right")
		axs[1][1].set_ylabel("# tasks",fontsize=14)
		axs[1][1].set_title("Round Robin",fontsize=16)


		axs[2][0].plot(np.arange(0,sim_time/1000,0.001),load_ed_rd[0],'-b' ,label="ED0")
		axs[2][0].plot(np.arange(0,sim_time/1000,0.001),load_ed_rd[1],'-r', label="ED1")
		axs[2][0].plot(np.arange(0,sim_time/1000,0.001),load_ed_rd[2],'-g', label="ED2")
		axs[2][0].plot(np.arange(0,sim_time/1000,0.001),load_ed_rd[3],'-c' , label="ED3")
		axs[2][0].plot(np.arange(0,sim_time/1000,0.001),load_ed_rd[4],'-m', label="ED4")
		axs[2][0].plot(np.arange(0,sim_time/1000,0.001),load_ed_rd[5],'-k', label="ED5")
		axs[2][0].plot(np.arange(0,sim_time/1000,0.001),load_ed_rd[6],'-y', label="ED6")
		axs[2][0].plot(np.arange(0,sim_time/1000,0.001),load_ed_rd[7],'-.b', label="ED7")
		axs[2][0].set_xlabel("simulation time (sec)",fontsize=14)
		axs[2][0].set_ylabel("# tasks", fontsize=14)
		axs[2][0].set_title("Random",fontsize=16)
		axs[2][0].legend(loc="upper right")

		axs[2][1].plot(np.arange(0,sim_time/1000,0.001),load_ed_lats[0],'-b' ,label="ED0")
		axs[2][1].plot(np.arange(0,sim_time/1000,0.001),load_ed_lats[1],'-r', label="ED1")
		axs[2][1].plot(np.arange(0,sim_time/1000,0.001),load_ed_lats[2],'-g', label="ED2")

		axs[2][1].plot(np.arange(0,sim_time/1000,0.001),load_ed_lats[3],'-c' , label="ED3")
		axs[2][1].plot(np.arange(0,sim_time/1000,0.001),load_ed_lats[4],'-m', label="ED4")
		axs[2][1].plot(np.arange(0,sim_time/1000,0.001),load_ed_lats[5],'-k', label="ED5")
		axs[2][1].plot(np.arange(0,sim_time/1000,0.001),load_ed_lats[6],'-y', label="ED6")
		axs[2][1].plot(np.arange(0,sim_time/1000,0.001),load_ed_lats[7],'-.b', label="ED7")
		axs[2][1].set_xlabel("simulation time (sec)",fontsize=14)
		axs[2][1].legend(loc="upper right")
		axs[2][1].set_ylabel("# tasks", fontsize=14)
		axs[2][1].set_title("LaTS",fontsize=16)


		orch_pf_ibot=orch[0][0].twinx()
		orch_pf_petrel=orch[0][1].twinx()
		orch_pf_lavea=orch[1][0].twinx()
		orch_pf_rr=orch[1][1].twinx()
		orch_pf_rd=orch[2][0].twinx()
		orch_pf_lats=orch[2][1].twinx()
		orch_pf_petrel.set_ylabel("probability of failure",fontsize=13)
		orch_pf_rr.set_ylabel("probability of failure",fontsize=13)
		orch_pf_lats.set_ylabel("probability of failure",fontsize=13)

		orch_pf_ibot.plot(time_x,pf_ibdash_av, "g-", markevery=10,label="PF")
		orch_pf_petrel.plot(time_x_petrel,pf_petrel_av, "g-", markevery=10,label="PF")
		orch_pf_lavea.plot(time_x_lavea,pf_lavea_av, "g-", markevery=10,label="PF")
		orch_pf_rr.plot(time_x_rr,pf_rr_av, "g-", markevery=10,label="PF")
		orch_pf_rd.plot(time_x_rd,pf_rd_av, "g-", markevery=10,label="PF")
		orch_pf_lats.plot(time_x_lats,pf_lats_av, "g-", markevery=10,label="PF")
		orch_pf_ibot.legend(loc='lower right')
		orch_pf_petrel.legend(loc='lower right')
		orch_pf_lavea.legend(loc='lower right')
		orch_pf_rr.legend(loc='lower right')
		orch_pf_rd.legend(loc='lower right')
		orch_pf_lats.legend(loc='lower right')


		print("============================service time =========================")
		print([average_service_time_ibdash,average_service_time_petrel,average_service_time_lavea, average_service_time_rr, average_service_time_rd, average_service_time_lats])
		
		plt.show()	

		label=["IBDASH","PETREL","LAVEA","RR","RD","LaTS"]
		hat = ["x","|",".","+","/","*"]
		data = [average_service_time_ibdash,average_service_time_petrel,average_service_time_lavea,average_service_time_rr,average_service_time_rd, average_service_time_lats]
		plt.xticks(range(len(data)),label)
		plt.xlabel('Orchaestration scheme')
		plt.ylabel('Average service time (sec)')
		for i in range(len(data)):
			plt.bar(i, data[i], hatch=hat[i]) 
		plt.show()


		pf_ibdash_av=sum(pf_ibdash_av)/len(task_time)
		pf_petrel_av=sum(pf_petrel_av)/len(task_time)
		pf_lavea_av=sum(pf_lavea_av)/len(task_time)
		pf_rr_av=sum(pf_rr_av)/len(task_time)
		pf_rd_av=sum(pf_rd_av)/len(task_time)
		pf_lats_av=sum(pf_lats_av)/len(task_time)
		print("=====================================average pf ================================")
		print([pf_ibdash_av, pf_petrel_av, pf_lavea_av, pf_rr_av, pf_rd_av, pf_lats_av])


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
		pf.set_ylabel("Probability of failure for EDs",fontsize=14)
		pf.set_xlabel("Time passed (sec)",fontsize=14)
		pf.set_title('a')

		label=["IBDASH","PETREL","LAVEA","RR","RD","LaTs"]
		data = [pf_ibdash_av,pf_petrel_av,pf_lavea_av,pf_rr_av,pf_rd_av,pf_lats_av]
		plt.xticks(range(len(data)),label)
		plt.xlabel('Orchaestration Scheme',fontsize=14)
		plt.ylabel('Average probability of failure',fontsize=14)
		plt.title('b')
		for i in range(len(data)):
			plt.bar(i, data[i], hatch=hat[i]) 
		plt.subplots_adjust(left=0.1,bottom=0.1,right=0.91,top=0.9,hspace=0.4)
		plt.show()

		# Following data are retrieved from running the above script at different settings

		label=["IBDASH","PETREL","LAVEA","RR","RD","LaTs"]
		pf_mix=[0.17307748173921192, 0.36260435156650367, 0.3002251055481308, 0.4427271936210497, 0.3769879558146891, 0.2984016697509398]
		pf_ped=[0.4420294950020642, 0.8998949159772368, 0.8258736251837017, 0.9579308989360253, 0.9133802614616812, 0.8461783190029275]
		pf_ced=[0.08059456640349111, 0.15112762626958592, 0.15856629155589683, 0.19055400347090778, 0.16148370804254858, 0.12644346165911916]

		x_axis = np.arange(len(label))
		plt.bar(x_axis-0.3, pf_mix, 0.25, label="mix", hatch="*")
		plt.bar(x_axis,     pf_ced, 0.25, label="ced", hatch="x")
		plt.bar(x_axis+0.3, pf_ped, 0.25, label="ped", hatch="/")
		plt.xticks(x_axis, label, fontsize=14)
		plt.ylabel("Average PF for an application instance",fontsize=14)
		plt.legend(fontsize=14)
		plt.show()

		label=["IBDASH","PETREL","LAVEA","RR","RD","LaTs"]
		mix=[1.675176, 2.206585000000001, 2.4047309999999977, 3.074325999999993, 2.488698999999998, 1.0929739999999977]
		ped=[1.9368130000000001, 2.2033390000000024, 2.4208249999999993, 3.0776799999999938, 2.472324999999999, 1.0999780000000003]
		ced=[1.667073999999999, 2.205128000000002, 2.4282349999999995, 3.074460999999999, 2.475105999999999, 1.1587660000000002]
		x_axis = np.arange(len(label))
		plt.bar(x_axis-0.3, mix, 0.25, label="mix", hatch="-")
		plt.bar(x_axis,     ced, 0.25, label="ced", hatch="x")
		plt.bar(x_axis+0.3, ped, 0.25, label="ped", hatch="|")
		plt.xticks(x_axis, label, fontsize=14)
		plt.ylabel("Average service time (sec)",fontsize=14)
		plt.legend(fontsize=14)
		plt.show()

		fig1, li = plt.subplots(1,2,figsize=(11,5))
		dum = [0.038,    0.069, 0.091, 0.118, 0.148]
		inv = [0.051,    0.086, 0.12,  0.168, 0.22]
		in_dum = [0.038, 0.078, 0.11,  0.156, 0.188]
		dum_in = [0.051, 0.07,  0.1,   0.135, 0.169]
		real = [0.038, 0.12,0.19,0.27,0.352]
		add=[0.038,0.147, 0.201, 0.274,0.336]
		tk0=[96, 32.4, 47.4]
		tk1=[0.01, 0.01, 26.7]
		tk2=[0.01, 34.6, 0.01]
		dum_ph =[0.0025, 0.012, 0.020, 0.028, 0.034]
		inv_ph =[0.0028, 0.0065, 0.015, 0.024, 0.033]
		in_dum_ph = [0.0028,0.0073, 0.0129, 0.021, 0.030]
		dum_in_ph = [0.0034, 0.0081, 0.016,0.024, 0.032]
		real_ph = [0.0028, 0.0155,0.029, 0.047,0.066]
		add_ph=[0.0053,0.018, 0.035, 0.052, 0.067]
		tk_x = [1,2,3]
		x=[0 , 1, 2, 3, 4]
		x_ph=[0 , 1, 2, 3, 4]
		li[0].scatter(x,dum,color='r')
		#li[0].scatter(x,inv,color='b')
		#li[0].scatter(x,in_dum,color='g')
		li[0].scatter(x,dum_in,color='m')
		#li[0].scatter(x,real,color="y")
		#li[0].scatter(x,add,color="c")
		label_tk=["t0:1 t1:0 t2:0","t0:2 t1:0 t2:1","t0:1 t1:1 t2=0"]
		axis_tk = np.arange(len(label_tk))
		#print(axis_tk)
		li[1].bar(axis_tk-0.2,tk0, 0.15, label="t0", hatch="x")
		li[1].bar(axis_tk,tk1, 0.15, label="t1", hatch="|")
		li[1].bar(axis_tk+0.2,tk2, 0.15, label="t2", hatch="*")
		li[1].set_xticks(axis_tk)
		li[1].set_xticklabels(label_tk)
		li[1].set_ylabel("CPU usage (%)",fontsize=14)
		#li[1].scatter(x_ph,dum_ph,color='r')
		#li[1].scatter(x_ph,inv_ph,color='b')
		#li[1].scatter(x_ph,in_dum_ph,color='g')
		#li[1].scatter(x_ph,dum_in_ph,color='m')
		#li[1].scatter(x_ph,real_ph,color="y")
		#li[1].scatter(x_ph,add_ph,color="c")
		
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

		z1_ph = np.polyfit(x_ph,dum_ph,1)
		z2_ph = np.polyfit(x_ph,inv_ph,1)
		z3_ph = np.polyfit(x_ph,in_dum_ph,1)
		z4_ph = np.polyfit(x_ph,dum_in_ph,1)
		z5_ph = np.polyfit(x_ph,real_ph,1)
		z6_ph = np.polyfit(x_ph,add_ph,1)
		p1_ph = np.poly1d(z1_ph)
		p2_ph = np.poly1d(z2_ph)
		p3_ph = np.poly1d(z3_ph)
		p4_ph = np.poly1d(z4_ph)
		p5_ph = np.poly1d(z5_ph)
		p6_ph = np.poly1d(z6_ph)

		li[0].plot(x,p1(x),"r--",label=r'$T(t_1,k*t_1)$')
		#li[0].plot(x,p2(x),"b--",label=r'$T(t_2,k*t_2)$')
		#li[0].plot(x,p3(x),"g--",label=r'$T(t_1,k*t_2)$')
		li[0].plot(x,p4(x),"m--",label=r'$T(t_2,k*t_1)$')
		#li[0].plot(x,p5(x),"y--",label=r'$T_{t2}(j*t_1,k*t_2)$')
		#li[0].plot(x,p6(x),"c--",label=r'$T(t_2,j*t_1)+T(t_2,k*t_2)$')

		#li[1].plot(x_ph,p1_ph(x_ph),"r--",label=r'$T(t_1,k*t_1)$')
		#li[1].plot(x_ph,p2_ph(x_ph),"b--",label=r'$T(t_2,k*t_2)$')
		#li[1].plot(x_ph,p3_ph(x_ph),"g--",label=r'$T(t_1,k*t_2)$')
		#li[1].plot(x_ph,p4_ph(x_ph),"m--",label=r'$T(t_2,k*t_1)$')
		#li[1].plot(x_ph,p5_ph(x_ph),"y--",label=r'$T_{t2}(j*t_1,k*t_2)$')
		#li[1].plot(x_ph,p6_ph(x_ph),"c--",label=r'$T(t_2,j*t_1)+T(t_2,k*t_2)$')
		li[0].legend(loc="upper left")
		li[1].legend(loc="upper right")
		li[0].set_title("a")
		li[1].set_title("b")
		#li[1].set_title("b")
		li[0].set_ylabel("Average service time(s)",fontsize=14)
		li[0].set_xlabel("k, j (# of interfering tasks already running)",fontsize=14)
		li[1].set_xlabel("number and type of tasks running",fontsize=14)
		#li[1].set_xlabel("k, j (# of interfering tasks already running) ")
		fig1.tight_layout()
		plt.show()
		fig, ax1 = plt.subplots()
		rep = [1,2,3,4,5,6,7,8,9]
		s_time = [2.65, 2.95, 3.06, 3.11, 3.11, 3.13, 3.13, 3.139, 3.13]
		pf = [0.567, 0.4567, 0.43, 0.402, 0.39, 0.34, 0.338, 0.333, 0.338]
		ax1.set_xlabel(r'Maximum number of replication $\gamma$', fontsize=14)
		ax1.set_ylabel('Average service time (s)',fontsize=14)
		ax1.plot(rep,s_time,'r-',label="Service time")
		ax1.legend(loc="upper left")
		ax2 = ax1.twinx()
		ax2.set_ylabel('Average probability of failure',fontsize=14)
		ax2.plot(rep,pf,'b-',label="Probability of failure")
		ax2.legend(loc="lower left")
		fig.tight_layout()
		plt.show()

		#print(ed0_latency)
"""	
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
