import argparse
import configparser
import json
import subprocess
import os
import sys
import paramiko
from scp import SCPClient
import time as timer


def createSSHClient(server, password):
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    if password.split(".")[1] == "pem":
        client.connect(server,username='ec2-user', key_filename=password)
    elif password.split(".")[1] == "johnny":
        client.connect(server,username='johnny')
    else:
        client.connect(server,username='xiang')
    client_scp = SCPClient(client.get_transport())
    return client_scp, client


scp_list_1=[]
ssh_list_1=[]
scp_list_2=[]
ssh_list_2=[]

#server_list = [("54.172.191.10","IBDASH_V2.pem"),("3.234.212.152","IBDASH_V2.pem"),("3.228.0.215","IBDASH_V2.pem")]

server_list1=[
              ("128.46.74.171",".xiang"),("128.46.74.172",".xiang"),("128.46.74.173",".xiang"),("128.46.74.95",".xiang"),
              ("128.46.74.170",".xiang"),("128.46.74.176",".xiang"),("128.46.74.174",".xiang"),("128.46.74.177",".xiang"),
              ("128.46.74.198",".xiang"),("128.46.74.197",".xiang"),("128.46.74.199",".xiang"),("128.46.74.191",".xiang"),
              ("10.165.77.168",".xiang"),("10.165.77.167",".xiang"),("10.165.77.166",".xiang"),("128.46.74.82",".xiang")]
#server_list1=[("128.46.74.95",".xiang")]
#server_list2=[]
server_list2=[("128.46.32.175",".johnny")]
#server_list1=[("128.46.74.198",".xiang")]
for each in server_list1:
    scp,ssh = createSSHClient(each[0],each[1])
    scp_list_1.append(scp)
    ssh_list_1.append(ssh)
print(ssh_list_1)
# client = paramiko.SSHClient()
# client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
# client.connect("128.46.32.175",username='johnny', key_filename="IBDASH_V2.pem")
# client_scp = SCPClient(client.get_transport())
for each in ssh_list_1:
    each.exec_command("rm ibdash/*.txt & rm ibdash/*.npy & rm ibdash/*.py & rm ibdash/*.json & rm ibdash/*.mp4 & rm ibdash/*.jpg & rm ibdash/*.csv")
    each.exec_command("kill $(lsof -t -i:5001)")

for each in scp_list_1:
    start = timer.time()
    # profiling for lightgbm 
    # each.put("/home/jonny/Documents/Research/IBDASH/profile_data/profile.py","/home/xiang/ibdash/")
    # each.put("/home/jonny/Documents/Research/IBDASH/profile_data/lightgbm/pca.py","/home/xiang/ibdash/")
    # each.put("/home/jonny/Documents/Research/IBDASH/profile_data/lightgbm/train_1.py","/home/xiang/ibdash/")
    # each.put("/home/jonny/Documents/Research/IBDASH/profile_data/lightgbm/train_2.py","/home/xiang/ibdash/")
    # each.put("/home/jonny/Documents/Research/IBDASH/profile_data/lightgbm/com_test.py","/home/xiang/ibdash/") 
    # each.put("/home/jonny/Documents/Research/IBDASH/profile_data/lightgbm/Digits_Train.txt","/home/xiang/ibdash/")
    # each.put("/home/jonny/Documents/Research/IBDASH/profile_data/lightgbm/Digits_Test.txt","/home/xiang/ibdash/")
    # each.put("/home/jonny/Documents/Research/IBDASH/profile_data/lightgbm/Digits_Train_Transform_0.txt","/home/xiang/ibdash/")
    # each.put("/home/jonny/Documents/Research/IBDASH/profile_data/lightgbm/lightGBM_model_1_0.txt","/home/xiang/ibdash/")
    # each.put("/home/jonny/Documents/Research/IBDASH/profile_data/lightgbm/lightGBM_model_2_0.txt","/home/xiang/ibdash/")
    # each.put("/home/jonny/Documents/Research/IBDASH/profile_data/lightgbm/Digits_Train_Transform_0.txt","/home/xiang/ibdash/")
    # each.put("/home/jonny/Documents/Research/IBDASH/profile_data/lightgbm/vectors_pca_0.npy","/home/xiang/ibdash/")

    # each.put("/home/jonny/Documents/Research/IBDASH/profile_data/cpu_profile.py","/home/xiang/ibdash/")
    # each.put("/home/jonny/Documents/Research/IBDASH/profile_data/tk_usage_profile.py","/home/xiang/ibdash/")
    # each.put("/home/jonny/Documents/Research/IBDASH/profile_data/matrix_app/tk0.py","/home/xiang/ibdash/")
    # each.put("/home/jonny/Documents/Research/IBDASH/profile_data/matrix_app/tk1.py","/home/xiang/ibdash/")
    # each.put("/home/jonny/Documents/Research/IBDASH/profile_data/matrix_app/tk2.py","/home/xiang/ibdash/")
    # each.put("/home/jonny/Documents/Research/IBDASH/profile_data/matrix_app/tk3.py","/home/xiang/ibdash/") 
    # each.put("/home/jonny/Documents/Research/IBDASH/profile_data/matrix_app/tk4.py","/home/xiang/ibdash/")
    # each.put("/home/jonny/Documents/Research/IBDASH/profile_data/matrix_app/tk0_output_0.npy","/home/xiang/ibdash/")  
    # each.put("/home/jonny/Documents/Research/IBDASH/profile_data/matrix_app/tk1_output_0.npy","/home/xiang/ibdash/")  
    # each.put("/home/jonny/Documents/Research/IBDASH/profile_data/matrix_app/tk2_output_0.npy","/home/xiang/ibdash/")  
    # each.put("/home/jonny/Documents/Research/IBDASH/profile_data/matrix_app/tk3_output_0.npy","/home/xiang/ibdash/")  
    # each.put("/home/jonny/Documents/Research/IBDASH/profile_data/matrix_app/tk4_output_0.npy","/home/xiang/ibdash/")  

 #   each.put("/home/jonny/Documents/Research/IBDASH/profile_data/lightgbm/Digits_Train.txt","/home/xiang/ibdash/")
 
    # each.put("/home/jonny/Documents/Research/IBDASH/profile_data/profile.py","/home/xiang/ibdash/")
    # each.put("/home/jonny/Documents/Research/IBDASH/profile_data/video_app/video_split.py","/home/xiang/ibdash/")
    # each.put("/home/jonny/Documents/Research/IBDASH/profile_data/video_app/extract_frame_1.py","/home/xiang/ibdash/")
    # each.put("/home/jonny/Documents/Research/IBDASH/profile_data/video_app/img_class_1.py","/home/xiang/ibdash/")
    # each.put("/home/jonny/Documents/Research/IBDASH/profile_data/video_app/extract_frame_2.py","/home/xiang/ibdash/")
    # each.put("/home/jonny/Documents/Research/IBDASH/profile_data/video_app/img_class_2.py","/home/xiang/ibdash/")
    # each.put("/home/jonny/Documents/Research/IBDASH/profile_data/video_app/extract_frame_3.py","/home/xiang/ibdash/")
    # each.put("/home/jonny/Documents/Research/IBDASH/profile_data/video_app/img_class_3.py","/home/xiang/ibdash/")
    # each.put("/home/jonny/Documents/Research/IBDASH/profile_data/video_app/gathering_result.py","/home/xiang/ibdash/")
    # each.put("/home/jonny/Documents/Research/IBDASH/profile_data/video_app/test.mp4","/home/xiang/ibdash/")

    # each.put("/home/jonny/Documents/Research/IBDASH/profile_data/video_app/test_1_of_3_0.mp4","/home/xiang/ibdash/")
    # each.put("/home/jonny/Documents/Research/IBDASH/profile_data/video_app/test_2_of_3_0.mp4","/home/xiang/ibdash/")
    # each.put("/home/jonny/Documents/Research/IBDASH/profile_data/video_app/test_3_of_3_0.mp4","/home/xiang/ibdash/")
    # each.put("/home/jonny/Documents/Research/IBDASH/profile_data/video_app/test_1_of_3_frame_1_0.jpg","/home/xiang/ibdash/")
    # each.put("/home/jonny/Documents/Research/IBDASH/profile_data/video_app/test_1_of_3_frame_2_0.jpg","/home/xiang/ibdash/")
    # each.put("/home/jonny/Documents/Research/IBDASH/profile_data/video_app/test_1_of_3_frame_1_result_0.txt","/home/xiang/ibdash/")
    # each.put("/home/jonny/Documents/Research/IBDASH/profile_data/video_app/test_1_of_3_frame_2_result_0.txt","/home/xiang/ibdash/")
    # each.put("/home/jonny/Documents/Research/IBDASH/profile_data/video_app/test_2_of_3_frame_1_0.jpg","/home/xiang/ibdash/")
    # each.put("/home/jonny/Documents/Research/IBDASH/profile_data/video_app/test_2_of_3_frame_2_0.jpg","/home/xiang/ibdash/")
    # each.put("/home/jonny/Documents/Research/IBDASH/profile_data/video_app/test_2_of_3_frame_1_result_0.txt","/home/xiang/ibdash/")
    # each.put("/home/jonny/Documents/Research/IBDASH/profile_data/video_app/test_2_of_3_frame_2_result_0.txt","/home/xiang/ibdash/")
    # each.put("/home/jonny/Documents/Research/IBDASH/profile_data/video_app/test_3_of_3_frame_1_0.jpg","/home/xiang/ibdash/")
    # each.put("/home/jonny/Documents/Research/IBDASH/profile_data/video_app/test_3_of_3_frame_2_0.jpg","/home/xiang/ibdash/")
    # each.put("/home/jonny/Documents/Research/IBDASH/profile_data/video_app/test_3_of_3_frame_1_result_0.txt","/home/xiang/ibdash/")
    # each.put("/home/jonny/Documents/Research/IBDASH/profile_data/video_app/test_3_of_3_frame_2_result_0.txt","/home/xiang/ibdash/")

    # each.put("/home/jonny/Documents/Research/IBDASH/profile_data/profile.py","/home/xiang/ibdash/")
    # each.put("/home/jonny/Documents/Research/IBDASH/profile_data/mapreduce/input_split.py","/home/xiang/ibdash/")
    # each.put("/home/jonny/Documents/Research/IBDASH/profile_data/mapreduce/map1.py","/home/xiang/ibdash/")
    # each.put("/home/jonny/Documents/Research/IBDASH/profile_data/mapreduce/map2.py","/home/xiang/ibdash/")
    # each.put("/home/jonny/Documents/Research/IBDASH/profile_data/mapreduce/map3.py","/home/xiang/ibdash/")
    # each.put("/home/jonny/Documents/Research/IBDASH/profile_data/mapreduce/map4.py","/home/xiang/ibdash/")
    # each.put("/home/jonny/Documents/Research/IBDASH/profile_data/mapreduce/reduce1.py","/home/xiang/ibdash/")
    # each.put("/home/jonny/Documents/Research/IBDASH/profile_data/mapreduce/reduce2.py","/home/xiang/ibdash/")
    # each.put("/home/jonny/Documents/Research/IBDASH/profile_data/mapreduce/combine.py","/home/xiang/ibdash/")

    # each.put("/home/jonny/Documents/Research/IBDASH/profile_data/mapreduce/split_input_1_0.csv","/home/xiang/ibdash/")
    # each.put("/home/jonny/Documents/Research/IBDASH/profile_data/mapreduce/split_input_2_0.csv","/home/xiang/ibdash/")
    # each.put("/home/jonny/Documents/Research/IBDASH/profile_data/mapreduce/split_input_3_0.csv","/home/xiang/ibdash/")
    # each.put("/home/jonny/Documents/Research/IBDASH/profile_data/mapreduce/split_input_4_0.csv","/home/xiang/ibdash/")
    # each.put("/home/jonny/Documents/Research/IBDASH/profile_data/mapreduce/split_output_1_0.json","/home/xiang/ibdash/")
    # each.put("/home/jonny/Documents/Research/IBDASH/profile_data/mapreduce/split_output_2_0.json","/home/xiang/ibdash/")
    # each.put("/home/jonny/Documents/Research/IBDASH/profile_data/mapreduce/split_output_3_0.json","/home/xiang/ibdash/")
    # each.put("/home/jonny/Documents/Research/IBDASH/profile_data/mapreduce/split_output_4_0.json","/home/xiang/ibdash/")
    # each.put("/home/jonny/Documents/Research/IBDASH/profile_data/mapreduce/us_result_0.json","/home/xiang/ibdash/")
    # each.put("/home/jonny/Documents/Research/IBDASH/profile_data/mapreduce/mainland_result_0.json","/home/xiang/ibdash/")
    # each.put("/home/jonny/Documents/Research/IBDASH/profile_data/mapreduce/covid_19_data.csv","/home/xiang/ibdash/")
    # each.put("/home/jonny/Documents/Research/IBDASH/profile_data/cpu_profile.py","/home/xiang/ibdash/")
    # each.put("/home/jonny/Documents/Research/IBDASH/profile_data/tk_usage_profile.py","/home/xiang/ibdash/")
    # each.put("/home/jonny/Documents/Research/IBDASH/profile_data/cpu_profile.py","/home/xiang/ibdash/")

    each.put("/home/jonny/Documents/Research/IBDASH/governer.py","/home/xiang/ibdash/")
    each.put("/home/jonny/Documents/Research/IBDASH/edge_list.json","/home/xiang/ibdash/")

    end = timer.time()
    print("transfer time: {}".format(end-start))
#server_list2=[]
for each in server_list2:
    scp,ssh = createSSHClient(each[0],each[1])
    scp_list_2.append(scp)
    ssh_list_2.append(ssh)

# client = paramiko.SSHClient()
# client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
# client.connect("128.46.32.175",username='johnny', key_filename="IBDASH_V2.pem")
# client_scp = SCPClient(client.get_transport())
for each in ssh_list_2:
    each.exec_command("rm ibdash/*.txt & rm ibdash/*.npy & rm ibdash/*.py & rm ibdash/*.json & rm ibdash/*.mp4 & rm ibdash/*.jpg & rm ibdash/*.csv")
    each.exec_command("kill $(lsof -t -i:5001)")

for each in scp_list_2:
    start = timer.time()
    #profiling for lightbgm
    # each.put("/home/jonny/Documents/Research/IBDASH/profile_data/profile.py","/home/johnny/ibdash/")
    # each.put("/home/jonny/Documents/Research/IBDASH/profile_data/lightgbm/pca.py","/home/johnny/ibdash/")
    # each.put("/home/jonny/Documents/Research/IBDASH/profile_data/lightgbm/train_1.py","/home/johnny/ibdash/")
    # each.put("/home/jonny/Documents/Research/IBDASH/profile_data/lightgbm/train_2.py","/home/johnny/ibdash/")
    # each.put("/home/jonny/Documents/Research/IBDASH/profile_data/lightgbm/com_test.py","/home/johnny/ibdash/") 
    # each.put("/home/jonny/Documents/Research/IBDASH/profile_data/lightgbm/Digits_Train.txt","/home/johnny/ibdash/")
    # each.put("/home/jonny/Documents/Research/IBDASH/profile_data/lightgbm/Digits_Test.txt","/home/johnny/ibdash/")
    # each.put("/home/jonny/Documents/Research/IBDASH/profile_data/lightgbm/lightGBM_model_1_0.txt","/home/johnny/ibdash/")
    # each.put("/home/jonny/Documents/Research/IBDASH/profile_data/lightgbm/lightGBM_model_2_0.txt","/home/johnny/ibdash/")
    # each.put("/home/jonny/Documents/Research/IBDASH/profile_data/lightgbm/Digits_Train_Transform_0.txt","/home/johnny/ibdash/")
    # each.put("/home/jonny/Documents/Research/IBDASH/profile_data/lightgbm/vectors_pca_0.npy","/home/johnny/ibdash/")

    # each.put("/home/jonny/Documents/Research/IBDASH/profile_data/cpu_profile.py","/home/johnny/ibdash/")
    # each.put("/home/jonny/Documents/Research/IBDASH/profile_data/tk_usage_profile.py","/home/johnny/ibdash/")
    # each.put("/home/jonny/Documents/Research/IBDASH/profile_data/matrix_app/tk0.py","/home/johnny/ibdash/")
    # each.put("/home/jonny/Documents/Research/IBDASH/profile_data/matrix_app/tk1.py","/home/johnny/ibdash/")
    # each.put("/home/jonny/Documents/Research/IBDASH/profile_data/matrix_app/tk2.py","/home/johnny/ibdash/")
    # each.put("/home/jonny/Documents/Research/IBDASH/profile_data/matrix_app/tk3.py","/home/johnny/ibdash/") 
    # each.put("/home/jonny/Documents/Research/IBDASH/profile_data/matrix_app/tk4.py","/home/johnny/ibdash/")
    # each.put("/home/jonny/Documents/Research/IBDASH/profile_data/matrix_app/tk0_output_0.npy","/home/johnny/ibdash/")  
    # each.put("/home/jonny/Documents/Research/IBDASH/profile_data/matrix_app/tk1_output_0.npy","/home/johnny/ibdash/")  
    # each.put("/home/jonny/Documents/Research/IBDASH/profile_data/matrix_app/tk2_output_0.npy","/home/johnny/ibdash/")  
    # each.put("/home/jonny/Documents/Research/IBDASH/profile_data/matrix_app/tk3_output_0.npy","/home/johnny/ibdash/")  
    # each.put("/home/jonny/Documents/Research/IBDASH/profile_data/matrix_app/tk4_output_0.npy","/home/johnny/ibdash/")  


    # each.put("/home/jonny/Documents/Research/IBDASH/profile_data/profile.py","/home/johnny/ibdash/")
    # each.put("/home/jonny/Documents/Research/IBDASH/profile_data/video_app/video_split.py","/home/johnny/ibdash/")
    # each.put("/home/jonny/Documents/Research/IBDASH/profile_data/video_app/extract_frame_1.py","/home/johnny/ibdash/")
    # each.put("/home/jonny/Documents/Research/IBDASH/profile_data/video_app/img_class_1.py","/home/johnny/ibdash/")
    # each.put("/home/jonny/Documents/Research/IBDASH/profile_data/video_app/extract_frame_2.py","/home/johnny/ibdash/")
    # each.put("/home/jonny/Documents/Research/IBDASH/profile_data/video_app/img_class_2.py","/home/johnny/ibdash/")
    # each.put("/home/jonny/Documents/Research/IBDASH/profile_data/video_app/extract_frame_3.py","/home/johnny/ibdash/")
    # each.put("/home/jonny/Documents/Research/IBDASH/profile_data/video_app/img_class_3.py","/home/johnny/ibdash/")
    # each.put("/home/jonny/Documents/Research/IBDASH/profile_data/video_app/gathering_result.py","/home/johnny/ibdash/")
    # each.put("/home/jonny/Documents/Research/IBDASH/profile_data/video_app/test.mp4","/home/johnny/ibdash/")

    # each.put("/home/jonny/Documents/Research/IBDASH/profile_data/video_app/test_1_of_3_0.mp4","/home/johnny/ibdash/")
    # each.put("/home/jonny/Documents/Research/IBDASH/profile_data/video_app/test_2_of_3_0.mp4","/home/johnny/ibdash/")
    # each.put("/home/jonny/Documents/Research/IBDASH/profile_data/video_app/test_3_of_3_0.mp4","/home/johnny/ibdash/")
    # each.put("/home/jonny/Documents/Research/IBDASH/profile_data/video_app/test_1_of_3_frame_1_0.jpg","/home/johnny/ibdash/")
    # each.put("/home/jonny/Documents/Research/IBDASH/profile_data/video_app/test_1_of_3_frame_2_0.jpg","/home/johnny/ibdash/")
    # each.put("/home/jonny/Documents/Research/IBDASH/profile_data/video_app/test_1_of_3_frame_1_result_0.txt","/home/johnny/ibdash/")
    # each.put("/home/jonny/Documents/Research/IBDASH/profile_data/video_app/test_1_of_3_frame_2_result_0.txt","/home/johnny/ibdash/")
    # each.put("/home/jonny/Documents/Research/IBDASH/profile_data/video_app/test_2_of_3_frame_1_0.jpg","/home/johnny/ibdash/")
    # each.put("/home/jonny/Documents/Research/IBDASH/profile_data/video_app/test_2_of_3_frame_2_0.jpg","/home/johnny/ibdash/")
    # each.put("/home/jonny/Documents/Research/IBDASH/profile_data/video_app/test_2_of_3_frame_1_result_0.txt","/home/johnny/ibdash/")
    # each.put("/home/jonny/Documents/Research/IBDASH/profile_data/video_app/test_2_of_3_frame_2_result_0.txt","/home/johnny/ibdash/")
    # each.put("/home/jonny/Documents/Research/IBDASH/profile_data/video_app/test_3_of_3_frame_1_0.jpg","/home/johnny/ibdash/")
    # each.put("/home/jonny/Documents/Research/IBDASH/profile_data/video_app/test_3_of_3_frame_2_0.jpg","/home/johnny/ibdash/")
    # each.put("/home/jonny/Documents/Research/IBDASH/profile_data/video_app/test_3_of_3_frame_1_result_0.txt","/home/johnny/ibdash/")
    # each.put("/home/jonny/Documents/Research/IBDASH/profile_data/video_app/test_3_of_3_frame_2_result_0.txt","/home/johnny/ibdash/")


    # each.put("/home/jonny/Documents/Research/IBDASH/profile_data/profile.py","/home/johnny/ibdash/")
    # each.put("/home/jonny/Documents/Research/IBDASH/profile_data/mapreduce/input_split.py","/home/johnny/ibdash/")
    # each.put("/home/jonny/Documents/Research/IBDASH/profile_data/mapreduce/map1.py","/home/johnny/ibdash/")
    # each.put("/home/jonny/Documents/Research/IBDASH/profile_data/mapreduce/map2.py","/home/johnny/ibdash/")
    # each.put("/home/jonny/Documents/Research/IBDASH/profile_data/mapreduce/map3.py","/home/johnny/ibdash/")
    # each.put("/home/jonny/Documents/Research/IBDASH/profile_data/mapreduce/map4.py","/home/johnny/ibdash/")
    # each.put("/home/jonny/Documents/Research/IBDASH/profile_data/mapreduce/reduce1.py","/home/johnny/ibdash/")
    # each.put("/home/jonny/Documents/Research/IBDASH/profile_data/mapreduce/reduce2.py","/home/johnny/ibdash/")
    # each.put("/home/jonny/Documents/Research/IBDASH/profile_data/mapreduce/combine.py","/home/johnny/ibdash/")
    # each.put("/home/jonny/Documents/Research/IBDASH/profile_data/cpu_profile.py","/home/johnny/ibdash/")

    # each.put("/home/jonny/Documents/Research/IBDASH/profile_data/mapreduce/split_input_1_0.csv","/home/johnny/ibdash/")
    # each.put("/home/jonny/Documents/Research/IBDASH/profile_data/mapreduce/split_input_2_0.csv","/home/johnny/ibdash/")
    # each.put("/home/jonny/Documents/Research/IBDASH/profile_data/mapreduce/split_input_3_0.csv","/home/johnny/ibdash/")
    # each.put("/home/jonny/Documents/Research/IBDASH/profile_data/mapreduce/split_input_4_0.csv","/home/johnny/ibdash/")
    # each.put("/home/jonny/Documents/Research/IBDASH/profile_data/mapreduce/split_output_1_0.json","/home/johnny/ibdash/")
    # each.put("/home/jonny/Documents/Research/IBDASH/profile_data/mapreduce/split_output_2_0.json","/home/johnny/ibdash/")
    # each.put("/home/jonny/Documents/Research/IBDASH/profile_data/mapreduce/split_output_3_0.json","/home/johnny/ibdash/")
    # each.put("/home/jonny/Documents/Research/IBDASH/profile_data/mapreduce/split_output_4_0.json","/home/johnny/ibdash/")
    # each.put("/home/jonny/Documents/Research/IBDASH/profile_data/mapreduce/us_result_0.json","/home/johnny/ibdash/")
    # each.put("/home/jonny/Documents/Research/IBDASH/profile_data/mapreduce/mainland_result_0.json","/home/johnny/ibdash/")
    # each.put("/home/jonny/Documents/Research/IBDASH/profile_data/mapreduce/covid_19_data.csv","/home/johnny/ibdash/")
    # each.put("/home/jonny/Documents/Research/IBDASH/profile_data/tk_usage_profile.py","/home/johnny/ibdash/")
    # each.put("/home/jonny/Documents/Research/IBDASH/profile_data/cpu_profile.py","/home/johnny/ibdash/")

    each.put("/home/jonny/Documents/Research/IBDASH/governer.py","/home/johnny/ibdash/")
    each.put("/home/jonny/Documents/Research/IBDASH/edge_list.json","/home/johnny/ibdash/")
#    each.put("/home/jonny/Documents/Research/IBDASH_V2/profile_data/lightgbm/Digits_Train.txt","/home/xiang/ibdash/")
    end = timer.time()
    print("transfer time: {}".format(end-start))


