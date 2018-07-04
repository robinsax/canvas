# coding: utf-8
'''
Error handling and response dispatch logic.
'''

from ..configuration import config
from ..utils import format_exception, logger, create_callback_registrar
from ..dictionaries import AttributedDict
from ..json_io import serialize_json
from .views import PageView, ErrorView
from .responses import create_json, create_page

log = logger(__name__)
on_error = create_callback_registrar()

def get_error_response(http_ex, source_ex, route, verb, context=None):
	'''
	Return an error response tuple given an `HTTPException`, the exception that
	caused the latter if applicable, and a request context if applicable. 
	'''
	#	Collect error info.
	error_dict = http_ex.get_info()
	if config.development.debug:
		context_repr = 'No request context'
		if context:
			context_repr = serialize_json(context, fallback=repr)
		error_dict['debug_info'] = {
			'traceback': format_exception(source_ex),
			'context': context_repr
		}
	
	#	Check whether this request occurred at an endpoint.
	in_api_realm = route.startswith('/%s'%(
		config.route_prefixes.api
	))

	#	Create an error diagnostic to pass to callbacks.
	error_data = AttributedDict(
		response=None,
		in_api_realm=in_api_realm,
		http_ex=http_ex,
		source_ex=source_ex,
		error_dict=error_dict,
		context=context
	)
	
	#	Invoke callbacks.
	try:
		on_error.invoke(error_data)
	except BaseException as ex:
		log.warn('Error handling callback errors:')
		log.warn(format_exception(ex))
	
	if error_data.response:
		#	A callback supplied a response.
		return error_data.response
	if in_api_realm or verb != 'get':
		#	Serve a JSON response.
		return create_json('error', error_dict, http_ex.status_code, 
				http_ex.headers)
	else:
		#	Serve a webpage response.
		page = PageView.resolved(' '.join((
			str(http_ex.status_code), http_ex.title
		)))
		page.page_views.append(ErrorView(error_dict))
		return create_page(page, http_ex.status_code, http_ex.headers)
