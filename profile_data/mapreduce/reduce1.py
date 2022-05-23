import pandas as pd
import os 
import time as timer
import json 
import random as rd
import argparse

def reducing(file1,file2,file3,file4,count):

	result1={}
	f1 = open(file1)
	f2 = open(file2)
	f3 = open(file3)
	f4 = open(file4)
	dic1 = json.load(f1)
	dic2 = json.load(f2)
	dic3 = json.load(f3)
	dic4 = json.load(f4)
	dic_list=[dic1,dic2,dic3,dic4]
	result1['Mainland China']={"Confirmed":0, "Deaths":0, "Recovered":0}
	for each in dic_list:
		result1['Mainland China']['Confirmed']+=each['Mainland China']['Confirmed']
		result1['Mainland China']['Deaths']+=each['Mainland China']['Deaths']
		result1['Mainland China']['Recovered']+=each['Mainland China']['Recovered']

	#with open(f"mainland_result_{count}.json","w") as outfile:
	with open(f"mainland_{count}_{rd.randint(1,10000)}.json","w") as outfile:
		json.dump(result1, outfile)

if __name__ =='__main__':

	parser = argparse.ArgumentParser()
	parser.add_argument('--count', type=int, help='instance_count')
	args = parser.parse_args()

	file1=f'split_output_1_{args.count}.json'
	file2=f'split_output_2_{args.count}.json'
	file3=f'split_output_3_{args.count}.json'
	file4=f'split_output_4_{args.count}.json'
	start=timer.time()
	reducing(file1,file2,file3,file4, args.count)
	end=timer.time()
	print("reduce1: "+str((end-start)))