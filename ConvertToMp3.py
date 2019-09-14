#!/home/dlarsen/.virtualenvs/Lore/bin/python
# encoding: utf-8
'''
ConvertToMp3 -- Converts a folder of wma files to mp3.

@author:     Daniel Larsen

@copyright:  2017 Daniel Larsen. All rights reserved.
'''

import sys
import os
import subprocess

from argparse import ArgumentParser

if __name__ == "__main__":

	parser = ArgumentParser()
	parser.add_argument("-d", "--directory", dest="directory", default=".",
		help="The directory to parse for media files.", metavar="DIR");

	args = parser.parse_args()

	for dirName, subdirList, fileList in os.walk(args.directory):
		for fname in fileList:
			if fname[-4:].lower() == ".wma":
				newName = fname.replace(".wma",".mp3")
				print("Replacing {} with {}".format(fname,newName))
				print(subprocess.check_output(['ffmpeg','-i',os.path.join(dirName,fname),'-acodec','libmp3lame',os.path.join(dirName,newName)]))
				os.remove(os.path.join(dirName,fname))
