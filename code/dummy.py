import numpy as np
import time as timer
total = 0
for i in range(0,100):
	start=timer.time()
	a= np.random.rand(1000,1000)
	b= np.random.rand(1000,1000)
	c = np.dot(a,b)
	end=timer.time()
	total += end-start
print(total/100)
