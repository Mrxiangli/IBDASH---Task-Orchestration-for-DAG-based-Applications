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
	vector_file=f"tk0_output_{args.count}.npy"
	#vector_file=f"tk0_output_0.npy"
	b=np.load(vector_file)
	id=np.identity(b.shape[0])
	for i in range(0,20):
		id = b@id
	vector_file=f"tk2_output_{args.count}.npy"
	#vector_file=f"tk2_output_{rd.randint(1,10000)}.npy"
	np.save(vector_file, id)
	end=timer.time()

	print("tk2: "+str((end-start)))