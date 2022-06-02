import cv2
from matplotlib import pyplot as plt
import time as timer
from numpy.linalg import inv
import argparse
import numpy as np
import random as rd

if __name__ =='__main__':

	# parser = argparse.ArgumentParser()
	# parser.add_argument('--count', type=int, help='instance_count')
	# args = parser.parse_args()

	start=timer.time()
	# input1=np.load(f"tk1_output_{args.count}.npy")
	# input2=np.load(f"tk3_output_{args.count}.npy")
	input1=np.load(f"tk1_output_0.npy")
	input2=np.load(f"tk3_output_0.npy")
	final = input1@input2
	#output = f"tk4_output_{args.count}.npy"
	output = f"tk4_output_{rd.randint(1,10000)}.npy"	
	np.save(output, final)
	end=timer.time()
	print("tk4: "+str((end-start)))