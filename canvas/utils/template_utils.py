#   config utf-8
'''
Utilities present in templates.
'''

import json as jsonlib
import jinja2

from urllib import parse

from jinja2 import Markup
from jinja2.exceptions import TemplateNotFound

from ...exceptions import (
	MacroParameterError, 
	UnsupportedEnformentMethod
)
from ..model import get_constraint
from .registration import register, callback
from ... import config

__all__ = [
	'markup',
	'markdown',
	'uri_encode',
	'json',
	'parameter_error',
	'get_client_validator',
	'describe_model_attr'
]

@register.template_filter
def markup(text):
	'''
	Transform the string `text` into markup that is 
	not escaped when rendered in a template.

	Available as a template filter.
	
	__Note__: Beware of XSS vulerabilities when using.
	'''
	return Markup(text)

@register.template_filter
def markdown(markdown, return_markup=True):
	'''
	Render a string as markdown.

	Available as a template filter.

	:markdown The string to render as markdown.
	:return_markup Whether or not to return a markup object
		that will not be escaped when rendered.
	'''
	rendered = markdown(markdown)
	if return_markup:
		return markup(rendered)
	return rendered

@register.template_filter
def uri_encode(s):
	'''
	Return `s` encoded as a a URI component.
	'''
	return parse.quote(s)

@register.template_filter
def json(o):
	'''
	Return the JSON representation of the
	JSON-serializable object `o`.
	'''
	return jsonlib.dumps(o)

@register.template_helper
def parameter_error(msg):
	'''
	Raise a `MacroParameterError` from within
	a template macro call.

	:msg The error message.
	'''
	raise MacroParameterError(msg)
del parameter_error

@register.template_helper
def get_client_validator(name):
	'''
	Return the client-serialized representation of
	the constraint called `name`, and it's error
	description.
	'''
	#	Retrieve the constraint.
	origin = get_constraint(name)

	if origin is not None:
		#	Try to get the client parsable representation.
		try:
			return {
				'repr': origin.as_client_parsable(),
				'error': origin.error_message
			}
		except UnsupportedEnformentMethod:
			#	The constraint called `name` doesn't
			#	support client-serialization.
			pass
	
	#	Return an empty validator.
	return {
		'repr': 'none:',
		'error': ''
	}
del get_client_validator

@register.template_helper
def describe_model_attr(model_cls, attr):
	'''
	Return the input type, name, validator name, and
	a best guess at a label as a dictionary for the model
	attribute `attr` of the model clas `model_cls`.

	Used for automatic form generation.
	'''
	#	Retrieve the column object.
	col = model_cls.__schema__[attr]

	return {
		'type': col.type.input_type,
		'name': attr,
		'label': ' '.join(attr.split('_')).title(),
		'validator': None if len(col.constraints) == 0 else col.constraints[0].name
	}
del describe_model_attr
