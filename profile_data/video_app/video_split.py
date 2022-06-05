from __future__ import print_function

import csv
import json
import math
import os
import shlex
import subprocess
from optparse import OptionParser
import time as timer
import random as rd


def get_video_length(filename):
		output = subprocess.check_output(("ffprobe", "-v", "error", "-show_entries", "format=duration", "-of",
																			"default=noprint_wrappers=1:nokey=1", filename)).strip()
		video_length = int(float(output))
		#print("Video length in seconds: " + str(video_length))

		return video_length


def ceildiv(a, b):
		return int(math.ceil(a / float(b)))


def split_by_seconds(filename, split_length, instance_count, vcodec="copy", acodec="copy", extra="", video_length=None, **kwargs):
		if split_length and split_length <= 0:
				print("Split length can't be 0")
				raise SystemExit
		#for profile		
		#instance_count=rd.randint(1,10000)
		
		if not video_length:
				video_length = get_video_length(filename)
		split_count = ceildiv(video_length, split_length)
		if split_count == 1:
				print("Video length is less then the target split length.")
				raise SystemExit

		split_cmd = ["ffmpeg","-y", "-i", filename, "-vcodec", vcodec, "-acodec", acodec, "-loglevel","0"] + shlex.split(extra)
		try:
				filebase = ".".join(filename.split(".")[:-1])
				fileext = filename.split(".")[-1]
		except IndexError as e:
				raise IndexError("No . in filename. Error: " + str(e))
		for n in range(0, split_count):
				split_args = []
				if n == 0:
						split_start = 0
				else:
						split_start = split_length * n

				split_args += ["-ss", str(split_start), "-t", str(split_length),
											 filebase + "_" + str(n + 1) + "_of_" +
											 str(split_count) + "_"+str(instance_count)+"." + fileext]
				#print("About to run: " + " ".join(split_cmd + split_args))
				subprocess.check_output(split_cmd + split_args)
		#remove this after profiling
		# rm_path=os.getcwd()
		# os.remove(os.path.join(rm_path,f"test_1_of_3_{instance_count}.mp4"))
		# os.remove(os.path.join(rm_path,f"test_2_of_3_{instance_count}.mp4"))
		# os.remove(os.path.join(rm_path,f"test_3_of_3_{instance_count}.mp4"))


def main():
		parser = OptionParser()
		
		parser.add_option("--count", 
											dest="instance_count",
											help="instance count",
											type="int",
											action="store"
											)
		parser.add_option("-s", "--split-size",
											dest="split_length",
											help="Split or chunk size in seconds, for example 10",
											type="int",
											action="store"
											)
		parser.add_option("-S", "--split-filesize",
											dest="split_filesize",
											help="Split or chunk size in bytes (approximate)",
											type="int",
											action="store"
											)
		parser.add_option("--chunk-strategy",
											dest="chunk_strategy",
											help="with --split-filesize, allocate chunks according to"
													 " given strategy (eager or even)",
											type="choice",
											action="store",
											choices=['eager', 'even'],
											default='eager'
											)

		parser.add_option("-v", "--vcodec",
											dest="vcodec",
											help="Video codec to use. ",
											type="string",
											default="copy",
											action="store"
											)
		parser.add_option("-a", "--acodec",
											dest="acodec",
											help="Audio codec to use. ",
											type="string",
											default="copy",
											action="store"
											)
		parser.add_option("-e", "--extra",
											dest="extra",
											help="Extra options for ffmpeg, e.g. '-e -threads 8'. ",
											type="string",
											default="",
											action="store"
											)
		(options, args) = parser.parse_args()
		
		filename="test.mp4"
		split_chunks=3

		def bailout():
				parser.print_help()
				raise SystemExit

		if not filename:
				bailout()

		else:
				video_length = None
				if not options.split_length:
						video_length = get_video_length(filename)
						file_size = os.stat(filename).st_size
						split_filesize = None
						if split_chunks:
								options.split_length = ceildiv(video_length, split_chunks)

				if not options.split_length:
						bailout()
				split_by_seconds(filename, video_length=video_length, **options.__dict__)


if __name__ == '__main__':
		start=timer.time()
		main()
		end=timer.time()
		print("video_split: "+str((end-start)))
