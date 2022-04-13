from numpy.linalg import inv
import time as timer
import numpy as np

start=timer.time()
for i in range(0,20):
	a= np.random.rand(5000,5000)
	b = a+a
end=timer.time()
print("tk5: "+str((end-start)/100))