import lightgbm as lgb
import boto3
import numpy as np
import time
import sys
import os
import time as timer

start=timer.time()

num_models = 2

path_parent = os.getcwd()
file_vector = "com_input/vectors_pca.txt.npy"
file_test = "com_input/Digits_Test.txt"

vectors = np.load(os.path.join(path_parent,file_vector))
test_data = np.genfromtxt(os.path.join(path_parent,file_test), delimiter="\t")

B = test_data[:,1:test_data.shape[1]]
MB = np.mean(B.T, axis=1)
CB = B - MB
PB = vectors.T.dot(CB.T)
first_n_B = PB.T[:,0:10].real

test_labels = test_data[:,0]
test_labels = test_labels.reshape(test_labels.shape[0],1)
y_test = test_labels

X_test = first_n_B

y_preds=[]

for i in range(1,num_models+1):
	filename = "com_input/models/lightGBM_model_"+str(i)+".txt"

	gbm = lgb.Booster(model_file=os.path.join(path_parent,filename))
	y_pred = gbm.predict(X_test, num_iteration=gbm.best_iteration)
	best_match=[]
	for k in range(len(y_test)):
		result = np.where(y_pred[k] == np.amax(y_pred[k]))[0]
		best_match.append(result)
	y_preds.append(best_match)
means = np.mean(y_preds, axis=0).round()
count_match=0

for i in range(len(y_test)):
	if means[i] == y_test[i]:
	   count_match = count_match +1
acc = count_match/len(y_pred)
end=timer.time()
print("com_test "+str((end-start)/100))