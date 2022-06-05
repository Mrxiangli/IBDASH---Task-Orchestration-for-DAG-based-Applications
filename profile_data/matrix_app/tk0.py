import cv2 
import numpy as np
import time as timer
from numpy.linalg import inv
import argparse
import configparser
import random as rd
import os


if __name__ =='__main__':
	parser = argparse.ArgumentParser()
	parser.add_argument('--count', type=int, help='instance_count')
	args = parser.parse_args()

	start=timer.time()
	a=np.random.rand(1000,1000)
	vector_output=f"tk0_output_{args.count}.npy"
	#vector_output=f"tk0_output_{rd.randint(1,10000)}.npy"
	np.save(vector_output,a)
	end=timer.time()

	print("tk1: "+str((end-start)))