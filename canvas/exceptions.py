#	coding utf-8
'''
Exception definitions.
'''

from .namespace import export

@export
class Failure(Exception): pass

@export 
class ConfigurationError(Exception): pass

@export
class AssetError(Exception): pass

@export
class Unrecognized(Exception): pass

@export
class TemplateNotFound(Exception): pass

@export
class TemplateOverlayError(Exception): pass

@export
class InvalidSchema(Exception): pass

@export
class InvalidConstraint(Exception): pass

@export
class InvalidQuery(Exception): pass

@export
class UnadaptedType(Exception): pass

@export
class IllegalEndpointRoute(Exception): pass

@export
class DependencyError(Exception): pass

@export
class ValidationErrors(Exception):
	
	def __init__(self, errors_or_summary, summary=None):
		if isinstance(errors_or_summary, str):
			self.errors, self.summary = False, errors_or_summary
		else:
			self.errors, self.summary = errors_or_summary, summary

	def	dictize(self):
		rep = dict()
		if self.errors:
			rep['errors'] = self.errors
		if self.summary:
			rep['summary'] = self.summary
		return rep

#	TODO: What's the deal with 'message' on these?
@export
class HTTPException(Exception):

	def __init__(self, title, status_code, message='', headers=None):
		super().__init__(message)
		self.title, self.status_code = title, status_code
		self.headers = headers
		self.diag = (self,)

	def response(self):
		return self.title, self.status_code, self.headers, None

@export
class BadRequest(HTTPException):

	def __init__(self, message):
		super().__init__('Bad Request', 400, message)

@export
class Unauthorized(HTTPException):

	def __init__(self, message='', realm=None):
		headers = {'WWW-Authenticate': 'Basic realm="%s"'%realm} if realm else None
		super().__init__('Unauthorized', 401, message, headers)

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

@export
class OversizeEntity(HTTPException):

	def __init__(self, size):
		super().__init__('Request Entity Too Large', 413, size, {
			'Retry-After': 0
		})

@export
class UnsupportedMediaType(HTTPException):

	def __init__(self, content_type):
		super().__init__('Unsupported Media Type', 415, content_type)

@export
class UnprocessableEntity(HTTPException):

	def __init__(self, message):
		super().__init__('Unprocessable Entity', 422, message)

@export
class InternalServerError(HTTPException):

	def __init__(self, reraise=False):
		super().__init__('Internal Server Error', 500)
		self.reraise = reraise
