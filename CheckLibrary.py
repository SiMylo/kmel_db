#!/home/dlarsen/.virtualenvs/Lore/bin/python
# encoding: utf-8
'''
CheckLibrary -- Checks a music library for missing tags and gives statistics.

@author:     Daniel Larsen, heavily borrowed from https://github.com/chrrrisw/kmel_db

@copyright:  2016 Daniel Larsen. All rights reserved.
'''

import sys
import os
import logging
import re
import subprocess

from argparse import ArgumentParser

from kmeldb.MediaFile import MediaFile
from kmeldb.DatabaseRegexConfig import DatabaseRegexConfig

from hsaudiotag import auto

log = logging.getLogger(__name__)
LGFMT = '%(levelname)-8s: %(filename)s:%(lineno)d - %(message)s'
logging.basicConfig(
		format=LGFMT,
		level=logging.INFO)

class TagIssue(object):
	"""
	Keeps track of all of the media library problems.
	"""

	def __init__(self, problemType, problemText, problemFile):
		self.problemType = problemType
		self.problemText = problemText
		self.problemFile = problemFile

	@property
	def problem(self):
		return self.problemType

	def __str__(self):
		"""
		Return a string to represent the problem.
		"""
		if self.problemText is not None:
			return "{}: {}\n\t{}".format(self.problemType, self.problemFile, self.problemText)
		else:
			return "{}: {}".format(self.problemType, self.problemFile)


if __name__ == "__main__":

	parser = ArgumentParser()
	parser.add_argument("-c", "--config", dest="config",
		help="The configuration file to use.", metavar="CONFIG");
	parser.add_argument("-d", "--directory", dest="directory", default=".",
		help="The directory to parse for media files.", metavar="DIR");
	parser.add_argument("-e", "--exclusions", dest="exclusions",
		help="Tells the program to print exclusion information", action="store_true")
	parser.add_argument("-g", "--listGenre", dest="listGenres", action="append",
		help="Tells the program to list all songs in the given group.", metavar="GENRE")
	parser.add_argument("-m", "--mp3gain", dest="checkMp3Gain",
		help="Tells the program to check for having applied mp3gain.", action="store_true")
	parser.add_argument("-p", "--playlists", dest="playlists",
		help="Tells the program to print specific playlist information", action="append")
	parser.add_argument("-s", "--statistics", dest="stats",
		help="Tells the program to print detailed statistics", action="store_true")
	parser.add_argument("-v", "--verbose", dest="verbose",
		help="Tells the program to print verbose information.", action="store_true")

	args = parser.parse_args()

	performers = {}
	albums = {}
	genres = {}
	tagProblems = []
	excluded = []
	config = DatabaseRegexConfig(args.config)

	numFiles = 0
	numFolders = 0
	maxFolderDepth = 0
	maxFilesInFolder = 0
	for root, dirs, files in os.walk(args.directory):
		numFolders += 1
		depth = os.path.relpath(root,args.directory).count(os.path.sep)+1
		if depth > maxFolderDepth:
			maxFolderDepth = depth
		if depth > 8:
			tagProblems.append(TagIssue("Deep Folder",None,filename))
		filesInFolder = 0
		for name in files:
			filesInFolder += 1
			numFiles += 1
			filename = os.path.join(root, name)

			if args.checkMp3Gain:
				# try:
				mp3output = subprocess.check_output(['mp3gain','-s','c',filename]).decode()
				albumGainResult = re.search(r'Recommended "Album" mp3 gain change: ([\-\d.]+)',mp3output)
				albumGain = 1000
				if albumGainResult:
					albumGain = float(int(albumGainResult.group(1)))
				trackGainResult = re.search(r'Recommended "Track" mp3 gain change: ([\-\d.]+)',mp3output)
				trackGain = 1000
				if trackGainResult:
					trackGain = float(int(trackGainResult.group(1)))
				mp3gainError = min(abs(albumGain),abs(trackGain))
				# except:
				# mp3gainError = 1000
				if (mp3gainError > 0.1):
					tagProblems.append(TagIssue("Gain Leveling Not Applied!","Tag Suggested Gain {}".format(mp3gainError),filename))

			if config.excluded(filename):
				if args.verbose or args.exclusions:
					print("Excluding file #{}: {}".format(numFiles, filename))
				excluded.append(filename)
			else:
				if args.verbose:
					print ("Processing file #{}: {}".format(numFiles, filename))
				else:
					print (".", end="", flush=True)
				metadata = auto.File(filename)
				performer = metadata.artist
				if performer != performer.split('/')[0]:
					tagProblems.append(TagIssue("Malformed Performer","{}->{}".format(performer,performer.split('/')[0]),filename))
				performer = performer.split('/')[0]
				if performer == "":
					tagProblems.append(TagIssue("Missing Performer",None,filename))
				if len(performer) > 64:
					tagProblems.append(TagIssue("Tag Too Big (performer)!","{}".format(performer),filename))
				if performer not in performers:
					performers[performer] = []
				performers[performer].append(filename)

				title = metadata.title
				title = config.filterTitle(title,performer)
				if title == "":
					title = 'Unknown'
					tagProblems.append(TagIssue("File doesn't have title tag!","Using {}".format(title),filename))
				if len(title) > 64:
					tagProblems.append(TagIssue("Tag Too Big (title)!","{}".format(title),filename))
				if args.verbose:
					print ("\t\'{}\'".format(title))


				album = metadata.album
				if album == "":
					album = 'Unknown'
					tagProblems.append(TagIssue("Missing Album!","Using {}".format(album),filename))
				if len(album) > 64:
					tagProblems.append(TagIssue("Tag Too Big (album)!","{}".format(album),filename))
				if album not in albums:
					albums[album] = []
				albums[album].append(filename)

				genre = metadata.genre
				if genre == "" or genre == "<Unknown>":
					tagProblems.append(TagIssue("Missing Genre!",None,filename))
				if len(genre) > 64:
					tagProblems.append(TagIssue("Tag Too Big (genre)!","{}".format(genre),filename))
				if genre not in genres:
					genres[genre] = []
				genres[genre].append(filename)

				track = metadata.track
				if name[:2] != ("%02d" % track) and name[:3] != ("%03d" % track):
					tagProblems.append(TagIssue("Track Mismatch!","Tagged Track: {}".format(track),filename))

				if len(metadata.year) > 64:
					tagProblems.append(TagIssue("ID3 year tag too long!","Tagged Track: {}".format(metadata.year),filename))
				if len(metadata.comment) > 64:
					tagProblems.append(TagIssue("ID3 comment tag too long!","Tagged Track: {}".format(metadata.comment),filename))


				config.addToGroup(MediaFile(index=numFiles,shortdir=album,shortfile=title,longdir=album,longfile=filename,discnumber=0,title=title,
					tracknumber=track,fullname=filename,performer=performer,album=album,genre=genre))

		if filesInFolder > maxFilesInFolder:
			maxFilesInFolder = filesInFolder
		if filesInFolder > 999:
			tagProblems.append(TagIssue("Too many files in folder!",None,filesInFolder))
	if numFiles > 20480:
		tagProblems.append(TagIssue("Too many files total!",None,numFiles))
	if numFolders > 999:
		tagProblems.append(TagIssue("Too many folders!",None,numFolders))

	print ("")
	tagProblems.sort(key=lambda x:x.problem)
	for issue in tagProblems:
		print (issue)
	config.finalizeGroups()
	playlists = config.makePlaylists()

	if args.stats:
		config.dumpGroups()
		print ("Dumping Genres: ")
		for genre in genres:
			print ("{}: {}".format(genre,len(genres[genre])))
		print ("Library checked for missing tags, long tags, file/folder count and depth.")
		if args.checkMp3Gain:
			print("Also checked that each file has been run through mp3gain.")
		print ("Excluded Files: {}".format(len(excluded)))
		print ("Total Files: {}".format(numFiles))
		print ("Total Folders: {}".format(numFolders))
		print ("Max Folder Depth: {}".format(maxFolderDepth))
		print ("Max Files In Folder: {}".format(maxFilesInFolder))

	for playlist in playlists:
		print ("{}: {}".format(playlist.name,len(playlist.media_files)))
	if args.playlists is not None:
		for playlist in playlists:
			if playlist.name in args.playlists:
				print("{}: {}".format(playlist.name,playlist.media_files))

	if args.listGenres:
		if args.listGenres[0] == "all":
			for genre in genres:
				print ("{}: {}".format(genre,genres[genre]))
		else:
			for genre in args.listGenres:
				print ("{}: {}".format(genre,genres[genre]))