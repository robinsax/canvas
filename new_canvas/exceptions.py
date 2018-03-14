#	coding utf-8
'''
Exception definitions.
'''

from .namespace import export

@export
class HTTPException(Exception):

	def __init__(self, title, status_code, message, headers=None):
		super().__init__(message)
		self.title, self.status_code = title, status_code
		self.headers = headers

	def response(self):
		return self.title, self.status_code, self.headers, None

@export
class NotFound(HTTPException):

	def __init__(self, path):
		super().__init__('Not Found', 404, path)

@export
class UnsupportedVerb(HTTPException):

	def __init__(self, verb, supported):
		super().__init__('Method Not Allowed', 405, verb, {
			'Allow': supported
		})
