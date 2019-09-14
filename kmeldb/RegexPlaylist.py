#!/home/dlarsen/.virtualenvs/Lore/bin/python
# encoding: utf-8
'''
RegexPlaylist -- Generates a kenwood music playlist based on a regex or set of regex.

@author:     Daniel Larsen, heavily borrowed from https://github.com/chrrrisw/kmel_db

@copyright:  2016 Daniel Larsen. All rights reserved.
'''

import random
import re
import copy
from .playlist import PlaylistFile

class RegexPlaylist(PlaylistFile):
	"""
	An object to hold a playlist. Uses a set of regex to add files and manipulate
	order.  This isn't strictly a playlist FILE, but I'm retrofitting it.
	"""

	def __init__(self, title, regex, excludes, groups):
			"""
			Store the name and initial regex.
			"""
			if regex:
				if type(regex) == str:
					self.regex = [regex]
				else:
					self.regex = regex
			else:
				self.regex = []

			if excludes:
				if type(excludes) == str:
					self.excludes = [excludes]
				else:
					self.excludes = excludes
			else:
				self.excludes = []

			self.title = title

			self._media_files = []
			self._randomized_files = None

			for group in groups:
				for innerGrouping in groups[group]:
					for song in groups[group][innerGrouping]:

						excluded = False
						for expr in self.excludes:
							if re.search(expr, song.fullname):
								excluded = True
								break

						if not excluded:
							for expr in self.regex:
								if re.search(expr, song.fullname):
									if group != 'ungrouped':
										self._media_files.append(groups[group])
									else:
										self._media_files.append(song)
									break

	@property
	def media_files(self):
		if self._randomized_files:
			return self._randomized_files

		files = []

		# DEEP COPY === VERY BAD BECAUSE OF write_db BEHAVIOR!
		# TODO: Note that the current implementation here will only allow a group to be
		# put in one playlist at a time.
		copiedList = self._media_files
		while len(copiedList) > 0 and len(files) < 9999:
			result = copiedList.pop(random.randrange(0,len(copiedList)))
			if type(result) == dict:
				if len(result.keys()) > 0:
					# print("Dict: {}".format(result.keys()))
					toTake = list(result.keys())[random.randrange(0,len(result.keys()))]
					temp = result.pop(toTake)
					# print("Pulled out {} of type {}".format(temp, type(temp)))
					# print("Now: {}".format(result.keys()))
					if len(result.keys()) > 0:
						# print("Appending: {}".format(result))
						# print("Putting it back")
						copiedList.append(result)
					if type(temp) == list:
						# print("Extending by: {}".format(temp))
						files.extend(temp)
						# print ("Now: {}".format(files))
					else:
						# print("Appending: {}".format(temp))
						files.append(temp)

			elif type(result) == list:
				# print("List, extending by: {}".format(result))
				files.extend(result)
			else:
				# print("Other, appending: {}".format(result))
				files.append(result)

		print("{} files in {} playlist!".format(len(files),self.title))
		# for media_file in files:
		# 	print("{} {}".format(media_file.index,media_file.longfile))

		return files

	@property
	def name(self):
		return self.title

	def add_media_file(self, media_file):
		self._media_files['ungrouped'].append(media_file)

	def add_media_group(self, group_name, files):
		self._media_files[group_name] = files