import numpy as np
import time as timer
import argparse
import random as rd

if __name__ =='__main__':

	# parser = argparse.ArgumentParser()
	# parser.add_argument('--count', type=int, help='instance_count')
	# args = parser.parse_args()

	start=timer.time()
	a= np.random.rand(2000,2000)
	#vector_file=f"tk0_output_{args.count}"
	vector_file=f"tk0_output_{rd.randint(1,10000)}"
	np.save(vector_file, a)
	end=timer.time()
	print("tk0: "+str((end-start)))
