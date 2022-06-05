import pandas as pd
import time as timer
import argparse
import configparser
import random as rd
import os

def split(file, count):

    result = pd.read_csv(file)
    interval = len(result)//4
    data_frame_1=(result[0:interval])
    data_frame_2=(result[interval:2*interval])
    data_frame_3=(result[interval*2:3*interval])
    data_frame_4=(result[interval*3:len(result)])
   
    #real case
    data_frame_1.to_csv(f"split_input_1_{count}.csv")
    data_frame_2.to_csv(f"split_input_2_{count}.csv")
    data_frame_3.to_csv(f"split_input_3_{count}.csv")
    data_frame_4.to_csv(f"split_input_4_{count}.csv")

    #for profiling
    # rand = rd.randint(1,10000)
    # f1=f"split_input_1_{rand}.csv"
    # f2=f"split_input_2_{rand}.csv"
    # f3=f"split_input_3_{rand}.csv"
    # f4=f"split_input_4_{rand}.csv"
    # data_frame_1.to_csv(f1)
    # data_frame_2.to_csv(f2)
    # data_frame_3.to_csv(f3)
    # data_frame_4.to_csv(f4)

    # os.remove(f1)
    # os.remove(f2)
    # os.remove(f3)
    # os.remove(f4)




if __name__ =='__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument('--count', type=int, help='instance_count')
    args = parser.parse_args()

    file='covid_19_data.csv'
    start=timer.time()
    split(file, args.count)
    #split(file, 0)
    end=timer.time()
    print("input_split: "+str((end-start)))