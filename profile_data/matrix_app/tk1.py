import cv2 
import numpy as np
import time as timer
from numpy.linalg import inv
import argparse
import configparser
import random as rd


if __name__ =='__main__':
	# parser = argparse.ArgumentParser()
	# parser.add_argument('--count', type=int, help='instance_count')
	# args = parser.parse_args()

	start=timer.time()
	#vector_file=f"tk0_output_{args.count}.npy"
	vector_file=f"tk0_output_0.npy"
	b=np.load(vector_file)
	c=b.T
	#vector_output=f"tk1_output_{args.count}.npy"
	vector_output=f"tk1_output_{rd.randint(1,10000)}.npy"
	np.save(vector_output,c)
	end=timer.time()
	print("tk1: "+str((end-start)))