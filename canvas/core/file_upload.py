# coding: utf-8
'''
File upload wrapping.
'''

from base64 import b64decode
#	TODO: Improve.

class FileUpload:

	def __init__(self, _file_obj):
		self._file_obj = _file_obj

	@property
	def mimetype(self):
		return self._file_obj.mimetype

	@property
	def filename(self):
		return self._file_obj.filename.strip()

	@property
	def ext(self):
		return self.filename.split('.')[-1]

	@property
	def data(self):
		data = b64decode(self._file_obj.read().split(b',')[1])
		self._file_obj.close()
		return data
	