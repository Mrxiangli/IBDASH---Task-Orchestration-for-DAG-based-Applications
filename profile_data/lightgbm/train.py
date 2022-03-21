import lightgbm as lgb
import boto3
import numpy as np
from boto3.s3.transfer import TransferConfig
import json
import random
import time
import os

import time as timer

start=timer.time()
path_parent = os.getcwd()
file = "train_input/Digits_Train_Transform.txt"
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
                early_stopping_rounds=5,
                verbose_eval=False)

y_pred = gbm.predict(X_train, num_iteration=gbm.best_iteration)
count_match=0
for i in range(len(y_pred)):
    result = np.where(y_pred[i] == np.amax(y_pred[i]))[0]
    if result == y_train[i]:
       count_match = count_match +1
acc = count_match/len(y_pred)
#model_name="lightGBM_model_1" + ".txt"
#gbm.save_model(model_name)
end=timer.time()
print("train1: "+str((end-start)/100))