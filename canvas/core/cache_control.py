#   config utf-8
'''
Cache control utilities used by the request handler for asset cache management.
'''

import datetime as dt

from ..utils.registration import callback

#   Declare exports (to request handler only).
__all__ = [
	'is_cache_valid',
	'get_cache_control_headers'
]

#   The `If-Modified-Since` header format.
IF_MODIFIED_SINCE_FORMAT = '%a, %d %b %Y %H:%M:%S %Z'
CACHE_TIME = 31536000

#   A datetime object containing the time the server was started as a benchmark
#   for client cache validation.
_started = None

@callback.pre_init
def mark_started():
	global _started
	_started = dt.datetime.now()
del mark_started

def is_cache_valid(modified_header):
	'''
	Return whether `modified_header` indicates a valid client cache.

	Will be ignored if canvas is in debug mode.
	'''
	check_modified_since = dt.datetime.strptime(modified_header, IF_MODIFIED_SINCE_FORMAT)
	return check_modified_since > _started

def get_cache_control_headers():
	'''
	Return cache control headers for the currently supported caching 
	mechanism(s).
	'''
	return {
		'Cache-Control': f'max-age={CACHE_TIME}'
	}
