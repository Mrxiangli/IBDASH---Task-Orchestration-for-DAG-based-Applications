import pandas as pd
import os 
import time as timer

start=timer.time()
df=pd.read_csv('baccalaureate2020.csv',low_memory=False)
result_frame_lt1000= df[df['pozitie_judet']<1000]
result_frame_gt1000= df[df['pozitie_judet']>1000]
path_parent = os.getcwd()
file_path1="output1/map1_lt1000.csv"  
file_path2="output2/map1_gt1000.csv" 
result_frame_lt1000.to_csv(os.path.join(path_parent,file_path1),index=False)
result_frame_gt1000.to_csv(os.path.join(path_parent,file_path2),index=False)
end=timer.time()
print("map1: "+str((end-start)/100))
