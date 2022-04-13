from numpy.linalg import inv
import time as timer
import numpy as np

start=timer.time()
for i in range(0,100):
	a= np.random.rand(1000,1000)
	b=a+a
	a_inv = inv(a)
end=timer.time()
print("tk3: "+str((end-start)/100))
