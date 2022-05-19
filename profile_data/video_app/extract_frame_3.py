from datetime import timedelta
import cv2
import numpy as np
import os
import time as timer
import argparse
import configparser

SAVING_FRAMES_PER_SECOND = 1

def format_timedelta(td):
	"""Utility function to format timedelta objects in a cool way (e.g 00:00:20.05) 
	omitting microseconds and retaining milliseconds"""
	result = str(td)
	try:
		result, ms = result.split(".")
	except ValueError:
		return result + ".00".replace(":", "-")
	ms = int(ms)
	ms = round(ms / 1e4)
	return f"{result}.{ms:02}".replace(":", "-")

def get_saving_frames_durations(cap, saving_fps):
	"""A function that returns the list of durations where to save the frames"""
	s = []
	# get the clip duration by dividing number of frames by the number of frames per second
	clip_duration = cap.get(cv2.CAP_PROP_FRAME_COUNT) / cap.get(cv2.CAP_PROP_FPS)
	# use np.arange() to make floating-point steps
	#for i in np.arange(, clip_duration, 1 / saving_fps):
	s=[clip_duration//2,clip_duration-1/saving_fps]
	return s

def main(video_file,instance_count):
	filename, _ = os.path.splitext(video_file)
	file_prefix='_'.join(filename.split('_')[:-1])
	cur_dir=os.getcwd()
	#filename += "-opencv"
	# make a folder by the name of the video file
	#if not os.path.isdir(filename):
	#	try:
	#		os.mkdir(filename)
	#	except:
	#		pass
	# read the video file    
	cap = cv2.VideoCapture(video_file)
	# get the FPS of the video
	fps = cap.get(cv2.CAP_PROP_FPS)
	# if the SAVING_FRAMES_PER_SECOND is above video FPS, then set it to FPS (as maximum)
	saving_frames_per_second = min(fps, SAVING_FRAMES_PER_SECOND)
	# get the list of duration spots to save
	saving_frames_durations = get_saving_frames_durations(cap, saving_frames_per_second)
	# start the loop
	count = 0
	frame_count = 1
	while True:
		is_read, frame = cap.read()
		if not is_read:
			# break out of the loop if there are no frames to read
			break
		# get the duration by dividing the frame count by the FPS
		frame_duration = count / fps
		try:
			# get the earliest duration to save
			closest_duration = saving_frames_durations[0]
		except IndexError:
			# the list is empty, all duration frames were saved
			break
		if frame_duration >= closest_duration:
			# uncomment following after profiling 
			cv2.imwrite(os.path.join(cur_dir, f"{file_prefix}_frame_{frame_count}_{instance_count}.jpg"), frame) 
			# drop the duration spot from the list, since this duration spot is already saved
			try:
				saving_frames_durations.pop(0)
			except IndexError:
				pass
			frame_count+=1
		# increment the frame count
		count += 1


if __name__ == "__main__":
	import sys
	parser = argparse.ArgumentParser()
	parser.add_argument('--count', type=int, help='instance_count')
	args = parser.parse_args()
	start=timer.time()
	filename=f"test_3_of_3_{args.count}.mp4"
	main(filename,args.count)
	end=timer.time()
	print("extract_frame_3: "+str((end-start)))
