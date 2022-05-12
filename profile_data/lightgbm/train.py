import lightgbm as lgb
#import boto3
import numpy as np
#from boto3.s3.transfer import TransferConfig
import json
import random
import time
import os
import argparse
import configparser
import time as timer

if __name__ =='__main__':
	parser = argparse.ArgumentParser()
	parser.add_argument('--count', type=int, help='instance_count')
	args = parser.parse_args()
	start=timer.time()*1000
	path_parent = os.getcwd()
	file = "Digits_Train_Transform_{}.txt".format(args.count)
	train_data = np.genfromtxt(os.path.join(path_parent,file),delimiter="\t")
	y_train = train_data[:,0]
	X_train = train_data[:,1:train_data.shape[1]]
	lgb_train = lgb.Dataset(X_train, y_train,params={'verbose': -1}, free_raw_data=False)
	chance = round(random.random()/2 + 0.5,1)
	params = {
		'boosting_type': 'gbdt',
		'objective': 'multiclass',
		'num_classes' : 10,
		'metric': {'multi_logloss'},
		'num_leaves': 50,
		'learning_rate': 0.05,
		'feature_fraction': 0.9,
		'bagging_fraction': chance, # If model indexes are 1->20, this makes feature_fraction: 0.7->0.9
		'bagging_freq': 5,
		'max_depth': 5,
		'verbose': -1,
		'num_threads': 16
	 }

	gbm = lgb.train(params,
					lgb_train,
					num_boost_round=100, # number of trees
					valid_sets=lgb_train,
					#verbose_eval=-1,
					#early_stopping_rounds = 5)
					callbacks=[lgb.log_evaluation(0)])
	lgb.early_stopping(stopping_rounds=5)
	lgb.log_evaluation()

	y_pred = gbm.predict(X_train, num_iteration=gbm.best_iteration)
	count_match=0
	for i in range(len(y_pred)):
		result = np.where(y_pred[i] == np.amax(y_pred[i]))[0]
		if result == y_train[i]:
		   count_match = count_match +1
	acc = count_match/len(y_pred)
	model_name="lightGBM_model_"+str(args.count) + ".txt"
	gbm.save_model(model_name)
	end=timer.time()*1000
	print("train1: "+str((end-start)//1000))
