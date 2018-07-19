# coding: utf-8
'''
File upload wrapping.
'''

from base64 import b64decode
#	TODO: Improve.

class FileUpload:

	def __init__(self, _file_obj, decode):
		self._file_obj = _file_obj
		self.decode = decode

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
		data = self._file_obj.read()
		if self.decode:
			data = b64decode(data.split(b',')[1])
		self._file_obj.close()
		return data
	