import json
import os
import mxnet as mx
from mxnet import gluon, nd
from mxnet.gluon.model_zoo import vision
import numpy as np
import time as timer
import argparse
import configparser

if __name__ =='__main__':
	
	parser = argparse.ArgumentParser()
	parser.add_argument('--count', type=int, help='instance_count')
	args = parser.parse_args()

	start=timer.time()
	temp_handle=[]

	while True: 
		if os.path.exists(f"test_1_of_3_frame_1_result_{args.count}.txt"):
			if os.path.exists(f"test_1_of_3_frame_2_result_{args.count}.txt"):
				if os.path.exists(f"test_2_of_3_frame_1_result_{args.count}.txt"):
					if os.path.exists(f"test_2_of_3_frame_2_result_{args.count}.txt"):
						if os.path.exists(f"test_3_of_3_frame_1_result_{args.count}.txt"):
							if os.path.exists(f"test_3_of_3_frame_2_result_{args.count}.txt"):
								temp_handle.append(open(f"test_1_of_3_frame_1_result_{args.count}.txt","r"))
								temp_handle.append(open(f"test_1_of_3_frame_2_result_{args.count}.txt","r"))
								temp_handle.append(open(f"test_2_of_3_frame_1_result_{args.count}.txt","r"))
								temp_handle.append(open(f"test_2_of_3_frame_2_result_{args.count}.txt","r"))
								temp_handle.append(open(f"test_3_of_3_frame_1_result_{args.count}.txt","r"))
								temp_handle.append(open(f"test_3_of_3_frame_2_result_{args.count}.txt","r"))
								break
	file=f"analytic_result_{args.count}.txt"
	f=open(file,"w")

	for each in temp_handle:
		f.write(each.read())
		f.write("\n")

	end=timer.time()
	for each in temp_handle:
		each.close()
	f.close()
	print("gathering_result: "+str((end-start)))