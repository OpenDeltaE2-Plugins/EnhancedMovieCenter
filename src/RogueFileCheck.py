﻿#
# Copyright (C) 2011 by Coolman & Swiss-MAD
#
# In case of reuse of this source code please do not remove this copyright.
#
#	This program is free software: you can redistribute it and/or modify
#	it under the terms of the GNU General Public License as published by
#	the Free Software Foundation, either version 3 of the License, or
#	(at your option) any later version.
#
#	This program is distributed in the hope that it will be useful,
#	but WITHOUT ANY WARRANTY; without even the implied warranty of
#	MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#	GNU General Public License for more details.
#
#	For more information on the GNU General Public License see:
#	<http://www.gnu.org/licenses/>.
#

from os.path import exists, isdir, join, splitext
from os import listdir

from glob import glob
#from Components.config import *

from . import _

global extRogue

extRogue = frozenset([".ap", ".cuts", ".cutsr", ".meta", ".sc", ".eit", ".ts_mp.jpg", ".gm", "dvd.cuts"])


class RogueFileCheck:
	def __init__(self, path, avoid=""):
		self.found = {}
		self.files = []
		if path is not None:
			self.checkPath(path, avoid)

	def getStatistics(self):
		strg = ""
		for key in self.found:
			strg += key + ": " + str(self.found[key]) + _(" files\n")
		if strg == "":
			strg = _("No rogue files found.")
		else:
			strg = _("Found rogue files:\n\n") + strg
		return strg

	def checkPath(self, path, avoid=""):
		from .CommonSupport import extMedia
		#TODO check performance
		if not exists(path) or path is avoid:
			return
		for p in listdir(path):
			fullpath = join(path, p)
			if isdir(fullpath):
				try:
					self.checkPath(fullpath)
				except:
					pass
			else:
				if exists(fullpath):
					# Is there an alternative to avoid a for loop in a for loop
					# Maybe we can use a dict e.x.: .ap = .ts.ap
					filepath, ext = splitext(fullpath)
					if ext.lower() in extRogue:
						for f in glob(filepath + '*'):
							if splitext(f)[1].lower() in extMedia:
								break
						else:
							# No matching media file found
							try:
								self.found[ext] += 1
							except:
								self.found[ext] = 1
							self.files.append(fullpath)

	def getDelFilesScript(self):
		strg = ""
		for file in self.files:
			strg += "rm \"" + file + "\"\n"
		return strg

	def getScript(self, path):
		strg = ""
		if path and exists(path):
			for file in self.files:
				strg += "\nmv \"" + file + "\" \"" + path + "\""
		else:
			for file in self.files:
				strg += "\nrm -f \"" + file + "\""
		return strg[1:]
