#   coding utf-8
'''
Utilities present in templates.
'''

import os
import re

from urllib import parse

from jinja2 import Markup
from markdown import markdown as render_markdown

from ..exceptions import (
	MacroParameterError, 
	UnsupportedEnforcementMethod,
	MarkdownNotFound
)
from .json_serializers import serialize_json
from .registration import register

#	Declare exports.
__all__ = [
	'normalize_whitespace',
	'markup',
	'markdown',
	'uri_encode',
	'json'
]

@register.template_filter
def normalize_whitespace(text):
	'''
	Replace all occurances of whitespace in `text` with a single space.
	'''
	return re.sub('\s+', ' ', text)

@register.template_filter
def markup(text):
	'''
	Transform the string `text` into markup that is not escaped when rendered 
	in a template.

	Beware of XSS vulnerabilities when using. In general, client-sourced data
	should always be escaped in templates.
	'''
	return Markup(text)

@register.template_filter
def markdown(markdown, return_markup=True):
	'''
	Render a string as markdown.

	Available as a template filter.

	:markdown The string to render as markdown.
	:return_markup Whether or not to return a markup object that will not be 
		escaped when rendered.
	'''
	rendered = render_markdown(markdown)
	if return_markup:
		return markup(rendered)
	return rendered

_markdown_cache = {}
@register.template_helper
def markdown_file(filename, return_markup=True):
	'''
	Load and render a file as markdown.

	Available as a template global.

	:filename The name of the markdown file to render, from `/markdown`.
	:return_markup Whether or not the output should be escaped when rendered 
		in Jinja.
	'''
	#	TODO: Fix these imports.
	from ..core.plugins import get_path_occurrences
	from .. import config
	
	#	Check cache.
	if filename in _markdown_cache:
		if return_markup:
			return markup(_markdown_cache[filename])
		return _markdown_cache[filename]

	#	Get file occurrences.
	paths = get_path_occurrences(os.path.join('assets', 'markdown', filename), filter=os.path.isfile)
	#	Assert an instance exists.
	if len(paths) == 0:
		raise MarkdownNotFound(filename)
	
	#	Load and render.
	with open(paths[-1], 'r') as f:
		rendered = render_markdown(f.read())

	if not config['debug']:
		#	Don't cache in debug mode.
		_markdown_cache[filename] = rendered
	
	if return_markup:
		return markup(rendered)
	return rendered

@register.template_filter
def uri_encode(text):
	'''
	Return `text` encoded as a a URI component.
	'''
	return parse.quote(text)

@register.template_filter
def json(obj, camelize_keys=False):
	'''
	Return the JSON representation of the JSON-serializable object `obj`.

	:camelize_props Whether to convert snake case keys to camel case.
	'''
	if not camelize_keys:
		return serialize_json(obj)
	
	def camelize(key):
		first, *other = key.split('_')
		return first + ''.join(o.capitalize() for o in other)

	def copy_one(one):
		#	Copy object, camelizing property case.
		if isinstance(one, (list, tuple)):
			return [copy_one(value) for value in one]
		elif isinstance(one, dict):
			return {camelize(k): copy_one(v) for k, v in one.items()}
		return one
	
	return serialize_json(copy_one(obj))
	
@register.template_helper
def parameter_error(msg):
	'''
	Raise a `MacroParameterError` from within a template macro call.

	:msg The error message.
	'''
	raise MacroParameterError(msg)
del parameter_error

@register.template_helper
def get_client_validator(name):
	'''
	Return the client-serialized representation of the constraint called 
	`name`, and its error description.
	'''
	from ..model import get_constraint

	#	Retrieve the constraint.
	origin = get_constraint(name)

	if origin is not None:
		#	Try to get the client parsable representation.
		try:
			return {
				'repr': origin.as_client_parsable(),
				'error': origin.error_message
			}
		except UnsupportedEnforcementMethod:
			#	The constraint called `name` doesn't
			#	support client-serialization.
			pass
	
	#	Return no validator.
	return None
del get_client_validator

@register.template_helper
def describe_model_attr(model_cls, attr):
	'''
	Return the input type, name, validator name, and a best guess at a label as
	a dictionary for the model attribute `attr` of the model clas `model_cls`.

	Used for automatic form generation.
	'''
	#	Retrieve the column object.
	col = model_cls.__schema__[attr]

	#	Find a validator.
	#	TODO: Triggers Jinja round-trip.
	validator = None
	for constraint in col.constraints:
		try:
			constraint.as_client_parsable()
			validator = constraint.name
			break
		except UnsupportedEnforcementMethod: pass

	return {
		'type': col.type.input_type,
		'name': attr,
		'label': ' '.join(attr.split('_')).title(),
		'validator': validator
	}
del describe_model_attr
