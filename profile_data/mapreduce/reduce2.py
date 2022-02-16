import pandas as pd
import os
import time as timer

start=timer.time()
path_parent = os.getcwd()
folder = "red2_input"
file_path = os.path.join(path_parent,folder)

df=[]
for each in os.listdir(file_path):
	part_df = pd.read_csv(os.path.join(file_path,each),index_col=None,header=0,low_memory=False)
	df.append(part_df)
frames = pd.concat(df,axis=0,ignore_index=True)
sort_frame = frames.sort_values(by=['pozitie_judet'])
sort_frame.to_csv('red2_result.csv',index=False)
end=timer.time()
print("reduce2: "+str((end-start)/100))