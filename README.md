# DAG based Task Orchestration - IBDASH

This repository contains the sample testing applications and the profiling data for those applications against 8 different AWS EC2 instances. To run the application, you will need to create the following envrioment. In our case, we used conda for this purposes.
To install anaconda through commandline, run the following command to retrieve the .sh file for conda

      wget https://repo.anaconda.com/archive/Anaconda3-2020.02-Linux-x86_64.sh

Then, creating a new conda enviroment 

      conda create -n ibdash python=3.7 anaconda
      
Then we need to install the related packages

      conda install -c conda-forge ffmpeg
      conda install -c conda-forge cpulimit
      pip install opencv-python-headless
      pip install mxnet
      
Note that some packages are used in the profiling stage, so they are not necessary for the orchestration process.

There are several hyper parameters that can be used to tune the simulation process

- --app app_name : this is used to select the application that we will run for the orchestration purposes, ie: matrix_app, video_app, mapreduce, lightgbm
- --mc mc_file.xlsx : this is used to specify the .xlsx file that we used to save the (m, c) value pairs, ie ED_mc_mt.xlsx, ED_mc_mr.xlsx, ED_mc_va.xlsx, ED_mc_gbm.xlsx
- --pf beta : this is a float number between 0 and 1 that indicates the probability of failure threshold
- --rd gamma : this is used to set the replication degree allowed
- --jp alpha : this is used to set the joint optimization parameter 

By default, the matrix application will be used for orchestration 

To run the application on real EC2 instance or real devices, the public ip of the instances need to be shared with the orchestrator. This can de done by generate ssh key and share is with orchesteator
