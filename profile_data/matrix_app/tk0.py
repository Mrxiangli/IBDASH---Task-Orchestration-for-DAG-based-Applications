import cv2 
import numpy as np
import time as timer
from numpy.linalg import inv

start=timer.time()
image = cv2.imread("testing_pic/panda.jpeg") 
image = cv2.cvtColor(src=image, code=cv2.COLOR_BGR2GRAY)

for i in range(0,100):
	a= np.random.rand(1000,1000)
	a_inv = inv(a)
end=timer.time()
print("tk0: "+str((end-start)/100))