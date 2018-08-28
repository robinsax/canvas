# coding: utf-8
'''
Dictizations are representations of models consiting of basic data structures 
such as dictionaries, lists, and primitive values.

Attributes can be added to the dictization of a model with the 
`dictized_property` class method decorator. Columns can be omitted by adding
`dictized=False` to their constructor.

To generate a dictization of a model, pass the model to `dictize`.
'''

from ...utils import cached_property
from ...json_io import json_serializer, serialize_json

#	Define a property name list that will be populated over the course of a 
#	model definition by the dictized_property decorator and cleared by the 
#	terminating model decorator.
_dictized_prop_cache = list()

def dictized_property(*args, **kwargs):
	'''
	A decorator for model methods that transforms them into a property that is
	dictized. This decorator can be used without trailing parenthesis or passed
	a flag indiciating whether or the decorated property should also be cached.
	'''
	is_cached = False
	
	#	Define the dictization resolution callable.
	def resolve(meth):
		name = meth.__name__
		#	Transform appropriately.
		if is_cached:
			meth = cached_property(meth)
		else:
			meth = property(meth)
		#	Add to map.
		_dictized_prop_cache.append(name)
		return meth
	
	#	Check usage and return appropriately.
	if kwargs:
		is_cached = kwargs.get('cached', False)
		return resolve
	else:
		return resolve(args[0])

def resolve_dictized_properties(model_cls):
	'''
	This function is invoked by the model decorator to resolve dictized 
	properties.
	'''
	for key in _dictized_prop_cache:
		#	Mark as dictized.
		model_cls.__dictized__.append(key)
	_dictized_prop_cache.clear()

def dictize(target, include=tuple(), omit=tuple()):
	'''Recursively return a dictization of `target`.''' 
	from .model import Model

	if isinstance(target, (list, tuple)):
		return [dictize(item, include, omit) for item in target]
	elif not issubclass(type(target), Model):
		#	Only models and iterables thereof are dictized.
		return target

	#	Compute the set of attribute names to dictize.
	column_set = target.__table__.columns.values()
	target_attrs = (attr for attr in (
		*(column.name for column in column_set if column.dictized),
		*(getattr(target, '__joined__', tuple())),
		*(target.__class__.__dictized__),
		*include
	) if attr not in omit and hasattr(target, attr))
	
	dictization = dict()
	for attr in target_attrs:
		#print(target, attr)
		dictization[attr] = dictize(getattr(target, attr), include, omit)
	return dictization
