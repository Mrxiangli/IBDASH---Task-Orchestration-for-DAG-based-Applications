import cv2
from matplotlib import pyplot as plt
import time as timer
from numpy.linalg import inv
import numpy as np

img = cv2.imread("testing_pic/panda.jpeg") 
img_gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

start=timer.time()
# This is a really bad trained set, I don't think it works at all...lol
panda_data = cv2.CascadeClassifier('testing_pic/panda.xml')

found = panda_data.detectMultiScale(img_gray,scaleFactor=1.3,minNeighbors=10,minSize =(100, 100))

amount_found = len(found)


if amount_found != 0:
	  
	# There may be more than one
	# sign in the image
	for (x, y, width, height) in found:
		  
		# We draw a green rectangle around
		# every recognized sign
		cv2.rectangle(img_rgb, (x, y), 
					  (x + height, y + width), 
					  (0, 255, 0), 5)
for i in range(0,5):
	a= np.random.rand(10000,10000)
plt.subplot(1, 1, 1)
end=timer.time()
print("tk4: "+str((end-start)/100))