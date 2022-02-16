import numpy as np
import time as timer

start=timer.time()
for i in range(0,100):
	a= np.random.rand(1000,1000)
	b= np.random.rand(1000,1000)
	c = np.dot(a,b)
end=timer.time()
print("tk2: "+str((end-start)/100))
