# DAG based Task Orchestration - IBDASH

This repository contains the sample testing applications and the profiling data for those applications against 8 different AWS EC2 instances. To run the application, you will need to create the following envrioment. In our case, we used conda for this purposes.
To install anaconda through commandline, run the following command to retrieve the .sh file for conda

      wget https://repo.anaconda.com/archive/Anaconda3-2020.02-Linux-x86_64.sh

Then, creating a new conda enviroment 

      conda create -n -ibdash python=3.7 anaconda
      
Then we need to install the related packages

      conda install -c conda-forge ffmpeg
      conda install -c conda-forge cpulimit
      pip install opencv-python-headless
      pip install mxnet
      
Note that some packages are used in the profiling stage, so they are not necessary for the orchestration process.



