#	coding utf-8
'''
Exceptions, because shit happens.
'''

#	TODO: Seperate model and controller exceptions?

#	Declare exports.
__all__ = [
	#	Special exceptions.
	'_Redirect',
	'ValidationErrors',
	#	HTTP exceptions.
	'HTTPException',
	'UnsupportedMethod',
	'RequestParamError',
	'UnknownAction',
	'NotFound',
	'ComponentNotFound',
	#	Other exceptions.
	'Unavailable',
	'TemplateNotFound',
	'ColumnDefinitionError',
	'MacroParameterError',
	'MarkdownNotFound',
	'PluginConfigError',
	'ConfigKeyError',
	'HeaderKeyError',
	'APIRouteDefinitionError',
	'TemplateOverlayError',
	'UnsupportedEnformentMethod',
	'InvalidQuery',
	'UnadaptedType'
]

class _Redirect(Exception):
	'''
	A class used internally as a redirection trigger.
	'''

	def __init__(self, target, code):
		self.target, self.code = target, code

class ValidationErrors(Exception):
	'''
	An error used to trigger an input validation error response.
	'''

	def __init__(self, error_dict):
		self.error_dict = error_dict

class HTTPException(Exception):
	'''
	An errors with a specific HTTP code (e.g. `500`, `404`, etc.).
	'''

	def __init__(self, message, code, desc):
		super().__init__(message)
		self.code, self.desc = (code, desc)

class RequestParamError(HTTPException):
	'''
	An error triggered by an incomplete request parameter set.
	'''

	def __init__(self, param):
		super().__init__(param, 400, 'Missing Request Parameter: %s'%param)

class UnknownAction(HTTPException):
	'''
	An error to raise when an invalid `action` parameter is specified in a 
	request. 
	'''
	
	def __init__(self, action):
		super().__init__(action, 400, 'Unknown Action: %s'%action)

class NotFound(HTTPException):
	'''
	An error used internally when an uncontrolled route is requested.
	'''

	def __init__(self, key):
		super().__init__(key, 404, 'Not Found')

class ComponentNotFound(HTTPException):
	'''
	An error used internally when an unavailable component is addressed.
	'''

	def __init__(self, component):
		super().__init__(component, 454, 'Component Not Found: %s'%component)

class UnsupportedMethod(HTTPException):
	'''
	An error used internally when an unsupported request method is used.
	'''

	def __init__(self):
		super().__init__('', 405, 'Unsupported Request Method')

class Unavailable(Exception):
	'''
	An error to be raised by components who do not want to be available for the
	handling of the current request.
	'''

class ColumnDefinitionError(Exception):
	'''
	An error raised when an invalid column type is declared.
	'''
	pass

class MacroParameterError(Exception):
	'''
	An exception raised by Jinja macros when they are supplied an invalid set of 
	parameters.
	'''
	pass

class MarkdownNotFound(Exception):
	'''
	An exception raised when a markdown file doesn't exist.
	'''
	pass

class PluginConfigError(Exception):
	'''
	An exception raised if a plugin modifies configuration incorrectly.
	'''
	pass

class ConfigKeyError(KeyError):
	'''
	An exception raised as the `KeyError` for `config`.
	'''
	pass

class HeaderKeyError(KeyError):
	'''
	An exception raised when a non-present header is retrieved.
	'''
	pass

class APIRouteDefinitionError(Exception):
	'''
	An exception raised when the route of an `APIEndpointController` isn't 
	prefixed with `api/`.
	'''
	pass

class TemplateNotFound(Exception):
	'''
	An exception raised when a template cannot be located for render.
	'''
	pass

class TemplateOverlayError(Exception):
	'''
	An exception raised when the `{% overlay %}` Jinja tag is used in a
	bottom-level template.
	'''
	pass

class UnsupportedEnformentMethod(Exception):
	'''
	An exception raised by constraints when an unsupported enforcement
	method is invoked.
	'''
	pass

class InvalidQuery(Exception):
	'''
	An exception raised when a `session.query()` is given invalid parameters.
	'''
	pass

class UnadaptedType(Exception):
	'''
	An exception raised when an unadaptable leaf is reached in an 
	`SQLExpression`.
	'''
	pass
