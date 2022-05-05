# computation intensive task with power method
import numpy as np	
import time
size = 100

A = np.random.random_sample((size,size))
start = time.time_ns()
for i in range(1000):
	A = A*A
end = time.time_ns()
print(f"duration: {(end-start)/1e6}")