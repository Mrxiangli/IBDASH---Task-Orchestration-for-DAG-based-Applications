import pandas as pd
import os 
import time as timer
import argparse
import json
import random as rd

def mapping(file, count):
    result={}
    df = pd.read_csv(file)
    for idx,row in df.iterrows():
        if row['Country/Region'] not in result.keys():
            result[row['Country/Region']]={"Confirmed":0,"Deaths":0,"Recovered":0}
            result[row['Country/Region']]["Confirmed"]+=row['Confirmed']
            result[row['Country/Region']]["Deaths"]+=row['Deaths']
            result[row['Country/Region']]["Recovered"]+=row['Recovered']
        else:
            result[row['Country/Region']]["Confirmed"]+=row['Confirmed']
            result[row['Country/Region']]["Deaths"]+=row['Deaths']
            result[row['Country/Region']]["Recovered"]+=row['Recovered']
  #  with open(f"split_output_2_{count}.json","w") as outfile:
    with open(f"split_output_2_{count}_{rd.randint(1,10000)}.json","w") as outfile:
        json.dump(result, outfile)



if __name__ =='__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument('--count', type=int, help='instance_count')
    args = parser.parse_args()

    file=f'split_input_2_{args.count}.csv'
    start=timer.time()
    mapping(file, args.count)
    end=timer.time()
    print("map2: "+str((end-start)))
