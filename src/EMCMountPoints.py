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
from os.path import dirname, ismount, realpath
from enigma import eTimer
from Components.config import config
from .EMCTasker import emcTasker


class EMCMountPoints:
	def __init__(self):
		self.mountPointDeviceCache = {}

		self.postWakeHDDtimer = eTimer()
		self.postWakeHDDtimer.callback.append(self.postWakeHDDtimerTimeout)

		self.postWakeHDDtimerActive = False
		self.postWakeHDDtimerDevice = ""

	def mountpoint(self, path, first=True):
		if first:
			path = realpath(path)
		if ismount(path) or len(path) == 0:
			return path
		return self.mountpoint(dirname(path), False)

	def getMountPointDevice(self, path):
		from Components.Harddisk import getProcMounts
		procMounts = getProcMounts()
		device = ""
		for x in procMounts:
			for entry in x:
				if path == entry:
					device = x[0]
		return device

	def getMountPointDeviceCached(self, path):
		if path in self.mountPointDeviceCache:
			mountPointDevice = self.mountPointDeviceCache[path]
		else:
			mountPoint = self.mountpoint(path)
			mountPointDevice = self.getMountPointDevice(mountPoint)
			self.mountPointDeviceCache[path] = mountPointDevice
		return mountPointDevice

	def postWakeHDDtimerStart(self, path):
		self.postWakeHDDtimer.stop()
		self.postWakeHDDtimer.start(500 * int(config.usage.hdd_standby.value), True)  # within 50% of the configured standby time after waking the HDD, this timer indicates that the HDD is active (we know it better than the harddiskmanager)
		self.postWakeHDDtimerActive = True
		self.postWakeHDDtimerDevice = self.getMountPointDeviceCached(path)

	def postWakeHDDtimerTimeout(self):
		self.postWakeHDDtimer.stop()
		self.postWakeHDDtimerActive = False

	def isExtHDDSleeping(self, path, MovieCenterInst):
		isExtHDDSleeping = False
		device = self.getMountPointDeviceCached(path)
		if not (self.postWakeHDDtimerActive and self.postWakeHDDtimerDevice == device):
			try:
				from Components.Harddisk import harddiskmanager
				for hdd in harddiskmanager.HDDList():
					if device.startswith(hdd[1].getDeviceName()):
						isExtHDDSleeping = hdd[1].isSleeping()
						break
			except:
				pass
		return isExtHDDSleeping

	def wakeHDD(self, path, postWakeCommand):
		association = []
		association.append((postWakeCommand, path))
		#wake the device a path is residing on by reading a random sector
		emcTasker.shellExecute("dd if=`df " + path + " | awk 'NR == 2 {print $1}'` bs=4096 count=1 of=/dev/null skip=$[($[RANDOM] + 32768*$[RANDOM]) % 1048576];echo 'wakeDevice finished'", association, False)


mountPoints = EMCMountPoints()

#****************************************************************************************
