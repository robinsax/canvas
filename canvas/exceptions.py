#	coding utf-8
'''
Exceptions, because shit happens
'''

#	TODO: Cleanup

#	Imported to package level
__all__ = [
	'_Redirect',
	'TemplateNotFound',
	'HTTPException',
	'UnsupportedMethod',
	'RequestParamError',
	'UnknownAction',
	'NotFound',
	'ComponentNotFound',
	'ValidationErrors',
	'ColumnDefinitionError',
	'MacroParameterError',
	'PluginInitError',
	'MarkdownNotFound',
	'ConfigKeyError'
]

class _Redirect(Exception):

	def __init__(self, target, code):
		self.target, self.code = (target, code)

class HTTPException(Exception):
	'''
	Represents errors with specific HTTP codes
	(e.g. `500`, `404`, etc.)
	'''

	def __init__(self, msg, code, desc):
		super().__init__(msg)
		self.code, self.desc = (code, desc)

class RequestParamError(HTTPException):
	'''
	Indicates missing request parameters.
	Automatically returned as the `KeyError`
	replacement for `request` in `vars`
	'''

	def __init__(self, param):
		super().__init__(param, 400, 'Missing Request Parameter: %s'%param)

class UnknownAction(HTTPException):
	'''
	Indicated the action specified by the
	client is unknown to the dispatched
	controller
	'''
	
	def __init__(self, action):
		super().__init__(action, 400, 'Unknown Action: %s'%action)

class NotFound(HTTPException):
	'''
	Indicates the requested route is unmapped.
	Canonically, should never be raised unless
	you're abstracting routes
	'''

	def __init__(self, key):
		super().__init__(key, 404, 'Not Found')

class ComponentNotFound(HTTPException):
	'''
	Indicates the component to which the request
	was addressed doesn't exist
	'''

	def __init__(self, component):
		super().__init__(component, 454, 'Component Not Found: %s'%component)

class UnsupportedMethod(HTTPException):
	'''
	Indicates the requested route does not support
	the request method. Should not be raised unless
	you're abstracting routes
	'''

	def __init__(self):
		super().__init__('', 405, 'Unsupported Request Method')

class ResourcePackagingError(Exception):
	'''
	Raised if resources are packaged incorrectly
	'''
	pass

class ValidationErrors(Exception):
	'''
	Raised when model constraints are violated
	by input.
	'''

	def __init__(self, error_dict):
		self.error_dict = error_dict

class PluginInitError(Exception):
	'''
	Raised when a plugin can't be initialized
	'''
	pass

class ColumnDefinitionError(Exception):
	'''
	Raised when an invalid column type is specified
	'''
	pass

class MacroParameterError(Exception):
	'''
	Raised by Jinja macros when they are supplied an invalid
	set of parameters
	'''
	pass

class MarkdownNotFound(Exception):
	'''
	Raised when a markdown file isn't found
	'''
	pass

class PluginConfigError(Exception):
	'''
	Raised if a plugin modifies configuration incorrectly.
	'''
	pass

class ConfigKeyError(KeyError):
	'''
	Raised as the `KeyError` for `config`.
	'''
	pass

class HeaderKeyError(KeyError):
	'''
	Raised as the `KeyError` for the `headers` dict
	in the request context
	'''

class APIRouteDefinitionError(Exception):
	'''
	Raised when the route of an `APIEndpointController`
	isn't prefixed with `api/`
	'''
	pass

class TemplateNotFound(Exception):
	pass

class TemplateOverlayError(Exception):
	pass

class UnsupportedEnformentMethod(Exception):
	pass

class MappedTypeError(Exception):
	pass