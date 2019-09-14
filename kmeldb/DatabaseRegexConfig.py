#!/home/dlarsen/.virtualenvs/Lore/bin/python
# encoding: utf-8
'''
DatabaseRegexConfig -- Tools used for applying my config to my music libarary scripts.

@author:     Daniel Larsen

@copyright:  2016 Daniel Larsen. All rights reserved.
'''

import os
import xml.etree.ElementTree as XmlTree
import re
from kmeldb.RegexPlaylist import RegexPlaylist

class DatabaseRegexConfig(object):

	def __init__(self, configFile):
		self.config = {"group": [], "playlist": [], "transform": [], "shorten": [], "exclude": []}
		if configFile is not None:
			if os.path.isfile(configFile):
				for child in XmlTree.parse(configFile).getroot():
					merged = False
					# Here we check if it's a valid type of configuration.
					if child.tag in self.config:
						# For groups and playlists, I want to be able to have multiples of them.
						# If there is already one here, merge the attributes (other than name).
						if child.tag == "group" or child.tag == "playlist":
							for parsed in self.config[child.tag]:
								if "name" in parsed and parsed["name"] == child.attrib["name"]:
									merged = True
									for attribute in child.attrib:
										if attribute != "name":
											if attribute in parsed:
												parsed[attribute].append(child.attrib[attribute])
											else:
												parsed[attribute] = [child.attrib[attribute]]
							# If there wasn't already a match, create a new one, using lists instead
							# of raw strings for attributes other than 'name'.
							if not merged:
								newTag = {}
								for attribute in child.attrib:
									if attribute == "name":
										newTag[attribute] = child.attrib[attribute]
									else:
										newTag[attribute] = [child.attrib[attribute]]
								self.config[child.tag].append(newTag)
						else:
							self.config[child.tag].append(child.attrib)
					else:
						print ("Warning: unrecognized tag! %s".format(child.tag))
			else:
				print ("Configuration file not found!")
		self.groups = {'ungrouped':{'nocapture':[]}}

	def excluded(self, filename):
		for expression in self.config["exclude"]:
			if re.search(expression["regex"],filename) is not None:
				return True
		return False

	def filterTitle(self, title, performer):
		for transform in self.config["transform"]:
			matches = re.search(transform["search"], title)
			if matches:
				replacement = transform["replace"]
				for substitution in re.findall('\$({[^{}]+}|\d+)',transform["replace"]):
					if "{Performer}" in substitution:
						replacement = replacement.replace("$"+substitution, performer)
					else:
						sub = int(substitution) if substitution.isdigit() else substitution
						if matches.group(sub) is None:
							print ("filterTitle({}, {}), ${} from {}".format(title, performer, sub, matches.groups()))
						replacement = replacement.replace("${}".format(sub), matches.group(sub))
				title = replacement

		for shorten in self.config["shorten"]:
			if re.search(shorten["search"], title):
				title = re.sub(shorten["search"], shorten["replace"], title)
		return title;

	def addToGroup(self, mediaFile):
		grouped = False
		for grouping in self.config["group"]:
			for regex in grouping["regex"]:
				result = re.search(regex, mediaFile.fullname)
				if result:
					grouped = True
					innerName = ''
					for group in result.groups():
						innerName += group
					if innerName == '':
						innerName = "noCapture"
					if grouping["name"] not in self.groups:
						self.groups[grouping["name"]] = {}
					if innerName not in self.groups[grouping["name"]]:
						self.groups[grouping["name"]][innerName] = [mediaFile]
					else:
						self.groups[grouping["name"]][innerName].append(mediaFile)

		if not grouped:
			self.groups['ungrouped']['nocapture'].append(mediaFile)

	def finalizeGroups(self):
		for group in self.groups:
			for innerGrouping in self.groups[group]:
				self.groups[group][innerGrouping].sort(key=lambda x:x.tracknumber)


	def dumpGroups(self):
		print ("Dumping Groups:")
		for group in self.groups:
			for innerName in self.groups[group]:
				print ("[{}][{}]: {}".format(group,innerName,len(self.groups[group][innerName])))
				# for song in self.groups[group][innerName]:
				# 	print ("{}".format(song.title))


	def makePlaylists(self):
		playlists = []
		for playlist in self.config["playlist"]:
			exclude = []
			regex = ['.*']
			if "exclude" in playlist:
				exclude = playlist["exclude"]
			if "regex" in playlist:
				regex = playlist["regex"]
			myPlaylist = RegexPlaylist(playlist["name"], regex, exclude, self.groups)
			playlists.append(myPlaylist)
		return playlists
