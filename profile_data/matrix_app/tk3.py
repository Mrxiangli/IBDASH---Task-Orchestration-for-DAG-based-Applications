from numpy.linalg import inv
import time as timer
import numpy as np
import argparse
import random as rd
import os

if __name__ =='__main__':
	parser = argparse.ArgumentParser()
	parser.add_argument('--count', type=int, help='instance_count')
	args = parser.parse_args()

	start=timer.time()
	input1=np.load(f"tk0_output_{args.count}.npy")
	input2=np.load(f"tk2_output_{args.count}.npy")
	# input1=np.load(f"tk0_output_0.npy")
	# input2=np.load(f"tk2_output_0.npy")
	final = (input1@input2).T
	output = f"tk3_output_{args.count}.npy"
	#output = f"tk3_output_{rd.randint(1,10000)}.npy"
	np.save(output, final)
	end=timer.time()

	print("tk3: "+str((end-start)))
