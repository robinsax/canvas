# coding: utf-8
'''
All of canvas's exceptions are packaged here.
'''

class InvalidSchema(Exception):
	'''Raised when the defined schema is recognized as invalid.'''
	pass

class InvalidQuery(Exception):
	'''Raised when a database query is recognized as invalid.'''
	pass

class InvalidTag(Exception):
	'''Raised when an invalid `Tag` is created.'''
	pass

class InvalidAsset(Exception):
	'''Raised when an invalid asset type is included on a page.'''
	pass

class AssetError(Exception):
	'''Raised when an error occurs while preparing an asset.'''
	pass

class Unrecognized(Exception):
	'''Used by deserializers to indicate they can't handle a given value.'''
	pass

class IllegalEndpointRoute(Exception):
	'''Raised when an un-prefixed API route is specified.'''
	pass

class DependencyError(Exception):
	'''Raised when a plugin dependency is not found.'''
	pass

class HTTPException(Exception):
	'''
	An exeception class associated to an error response to the client, with 
	an associated status code, header map, and diagonostic dictionary.
	'''

	def __init__(self, status_code, title, description=None, headers=None):
		'''
		Configure an overriding exception.
		::status_code The status code associated with the error.
		::title The title of this type of error.
		::description An additional description of the error.
		'''
		self.status_code = status_code
		self.title, self.description = title, description
		self.headers = headers

	def simple_response(self):
		'''Return a plaintext response tuple of this exeception.'''
		return self.title, self.status_code, None, 'text/plain'

	def get_info(self):
		'''
		Return a dictionary containing the information about this error that
		should be supplied to the client.
		'''
		info = {
			'code': self.status_code,
			'title': self.title
		}
		if self.description:
			info['description'] = self.description
		return info

	def maybe_report(self, log):
		'''Report this error in the log if configuration warrants.'''
		from .configuration import config
		from .utils import format_exception

		if self.status_code > 499 or config.development.log_client_errors:
			log.error(format_exception(ex))
	
	def __str__(self):
		return self.description

class BadRequest(HTTPException):
	'''An exception indicating a request was not understood.'''

	def __init__(self, description=None):
		super().__init__(400, 'Bad Request', description)

class Unauthorized(HTTPException):
	'''
	An exception indicating the client is not authorized to make the given 
	request.
	'''

	def __init__(self, description=None, realm=None):
		'''
		::realm The realm in which further requests should be authorized, if 
			any. Ignored if `authorization_method` is not specified in
			configuration.
		'''
		#	Clearly this import is circular.
		from .configuration import config

		#	Resolve the auth. scheme with which to inform the client.
		auth_scheme, headers = config.security.authorization_method, None
		if auth_scheme:
			if realm:
				auth_scheme = ' '.join((auth_scheme, 'realm="%s"'%realm))
			headers = {'WWW-Authenticate': auth_scheme}
		
		super().__init__(401, 'Unauthorized', description, headers)

class NotFound(HTTPException):
	'''An exception indicating the requested resource was not found.'''

	def __init__(self, path):
		super().__init__(404, 'Not Found', path)

class UnsupportedVerb(HTTPException):
	'''
	An exception indicating the current request verb is not supported on 
	this route.
	'''

	def __init__(self, which_verb, supported):
		'''
		::which_verb The attempted verb.
		::supported A list of verbs that are supported.
		'''
		super().__init__(405, 'Method Not Allowed', which_verb, {
			'Allow': ', '.join(verb.upper() for verb in supported)
		})

class OversizeEntity(HTTPException):
	'''
	An exception indicating that the body of a request exceeded the configured 
	maximum.
	'''

	def __init__(self, size):
		'''::size The content length of the request.'''
		super().__init__(413, 'Request Entity Too Large', size, {
			'Retry-After': 0
		})

class UnsupportedMediaType(HTTPException):
	'''An exception indicating the request's content type was invalid.'''

	def __init__(self, content_type):
		'''::content_type The content type of the request.'''
		super().__init__(415, 'Unsupported Media Type', content_type)

class UnprocessableEntity(HTTPException):
	'''
	An exception indicating that a request was understood but could not be 
	fufilled.
	'''

	def __init__(self, description=None):
		super().__init__(422, 'Unprocessable Entity', description)

class ValidationErrors(UnprocessableEntity):
	'''
	An exception indicating that one or more request parameters did not pass 
	validation. Raised when model constraints are violated.
	'''
	
	def __init__(self, errors, summary=None):
		'''
		::errors A parameter key, error description map.
		::summary A summary string.
		'''
		super().__init__()
		self.errors, self.summary = errors, summary

	def	get_info(self):
		info = super().get_info()
		info['errors'] = self.errors
		if self.summary:
			info['error_summary'] = self.error_summary
		return info

class InternalServerError(HTTPException):
	'''
	An exception indicating an error was encountered while handling the 
	request.
	'''

	def __init__(self, reraised_from=None):
		'''
		::is_reraise Whether or not this is a reraise of another exception.
		'''
		super().__init__(500, 'Internal Server Error')
		self.reraised_from = reraised_from
