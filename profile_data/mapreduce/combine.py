import pandas as pd
import os 
import time as timer
import json 
import random as rd
import argparse

def combine(file1,file2,count):

    result1={}
    f1 = open(file1)
    f2 = open(file2)
    dic1 = json.load(f1)
    dic2 = json.load(f2)
    dic_list=[dic1,dic2]

    with open(f"mapreduce_result_{count}.txt","w") as outfile:
    #with open(f"mapreduce_result_{count}_{rd.randint(1,10000)}.txt","w") as outfile:
        for each in dic_list:
            outfile.write(json.dumps(each))

if __name__ =='__main__':

    # real case
    parser = argparse.ArgumentParser()
    parser.add_argument('--count', type=int, help='instance_count')
    args = parser.parse_args()

    file1=f'mainland_result_{args.count}.json'
    file2=f'us_result_{args.count}.json'
    start=timer.time()
    combine(file1,file2, args.count)
    #combine(file1,file2, 0)
    end=timer.time()
    print("combine: "+str((end-start)))