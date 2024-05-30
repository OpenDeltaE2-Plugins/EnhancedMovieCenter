﻿from base64 import b64decode
from datetime import timedelta
from os.path import exists, getsize, join
from os import remove, stat as os_stat
from time import localtime, strftime
from Tools.Directories import fileExists

from mutagen.mp3 import MP3
from mutagen.easyid3 import EasyID3
from mutagen.id3 import ID3
from mutagen.flac import FLAC, Picture, error as FLACError
from mutagen.oggvorbis import OggVorbis
from mutagen.easymp4 import EasyMP4
from mutagen.mp4 import MP4
from mutagen.apev2 import APEv2File
from mutagen.aac import AAC

from .EMCTasker import emcDebugOut


def getAudioMetaData(service, ext):
	title = ""
	genre = ""
	artist = ""
	album = ""
	length = ""
	audio = None
	if fileExists("/tmp/.emcAudioTag.jpg"):
		remove("/tmp/.emcAudioTag.jpg")
	elif fileExists("/tmp/.emcAudioTag.jpeg"):
		remove("/tmp/.emcAudioTag.jpeg")
	elif fileExists("/tmp/.emcAudioTag.png"):
		remove("/tmp/.emcAudioTag.png")
	elif fileExists("/tmp/.emcAudioTag.gif"):
		remove("/tmp/.emcAudioTag.gif")
	if service:
		path = service.getPath()
		if ext.lower() == ".mp3":
			try:
				audio = MP3(join(path), ID3=EasyID3)
			except:
				audio = None
		elif ext.lower() == ".flac":
			try:
				audio = FLAC(join(path))
			except:
				audio = None
		elif ext.lower() == ".ogg":
			try:
				audio = OggVorbis(join(path))
			except:
				audio = None
		elif ext.lower() == ".mp4" or ext.lower() == ".m4a":
			try:
				audio = EasyMP4(join(path))
			except:
				audio = None
		# first for older mutagen-package(under 1.27)
		# APEv2 is tagged from tools like "mp3tag"
		# no tagging in new mutagen.aac
		elif ext.lower() == ".aac":
			try:
				audio = APEv2File(join(path))
			except:
				audio = None
		if audio:
			if ext.lower() != ".aac":
				length = str(timedelta(seconds=int(audio.info.length)))
			else:
				getlength = AAC(join(path))
				length = str(timedelta(seconds=int(getlength.info.length)))
			title = audio.get('title', [service.getPath()])[0]
			try:
				genre = audio.get('genre', [''])[0]
			except:
				genre = ""
			artist = audio.get('artist', [''])[0]
			album = audio.get('album', [''])[0]
			# now we try to get embedded covers
			if ext.lower() == ".mp3":
				try:
					scover = ID3(service.getPath())
				except:
					scover = None
				if scover:
					scovers = scover.getall("APIC")
					if len(scovers) > 0:
						try:
							ext = "." + scovers[0].mime.lower().split("/", -1)[1]
							writeTmpCover(scovers[0].data, ext)
						except Exception as e:
							emcDebugOut("[EMCMutagenSupport] Exception in Mp3EmbeddedCover: " + str(e))
			elif ext.lower() == ".flac":
				try:
					scover = audio.pictures
				except:
					scover = None
				if scover:
					if scover[0].data:
						try:
							ext = "." + scover[0].mime.lower().split("/", -1)[1]
							writeTmpCover(scover[0].data, ext)
						except Exception as e:
							emcDebugOut("[EMCMutagenSupport] Exception in FlacEmbeddedCover: " + str(e))
			elif ext.lower() == ".ogg":
				try:
					scover = audio
				except:
					scover = None
				if scover:
					for b64_data in scover.get("metadata_block_picture", []):
						try:
							data = b64decode(b64_data)
						except (TypeError, ValueError):
							continue

						try:
							picture = Picture(data)
						except FLACError:
							continue
						try:
							ext = "." + picture.mime.lower().split("/", -1)[1]
							writeTmpCover(picture.data, ext)
						except Exception as e:
							emcDebugOut("[EMCMutagenSupport] Exception in OggEmbeddedCover: " + str(e))
			elif ext.lower() == ".mp4" or ext.lower() == ".m4a":
				try:
					scover = MP4(service.getPath())
				except:
					scover = None
				if scover:
					try:
						scover = scover.get('covr', [''])[0]
						writeTmpCover(scover, ".jpg")
					except Exception as e:
						emcDebugOut("[EMCMutagenSupport] Exception in Mp4-M4aEmbeddedCover: " + str(e))

			return title, genre, artist, album, length

	return title, genre, artist, album, length


def writeTmpCover(data, ext):
	tmpCover = "/tmp/.emcAudioTag" + ext
	Cover = open(tmpCover, 'wb')
	Cover.write(data)
	Cover.close()


def getAudioFileSize(path):
	size = 0
	if not exists(path):
		return size
	try:
		if path:
			size += getsize(path)
			size /= (1024.0 * 1024.0)
	except Exception as e:
		emcDebugOut("[EMCMutagenSupport] Exception in getFileSize: " + str(e))
	return size


def getAudioFileDate(path):
	date = ""
	if not exists(path):
		return date
	try:
		if path:
			getdate = os_stat(path)
			# this way for translate the date in the right language
			# needed on Vti- or Pkt-images
			daystr = _(strftime('%A', localtime(getdate.st_mtime)))
			daynr = _(strftime('%d', localtime(getdate.st_mtime)))
			monthstr = _(strftime('%B', localtime(getdate.st_mtime)))
			year = _(strftime('%Y', localtime(getdate.st_mtime)))
			date = daystr + ", " + daynr + ". " + monthstr + " " + year
	except Exception as e:
		emcDebugOut("[EMCMutagenSupport] Exception in getFileDate: " + str(e))
	return date
