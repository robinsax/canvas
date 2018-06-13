# coding: utf-8
'''
Unit tests on the JSON API.
'''

from datetime import datetime

import canvas.tests as cvt

from canvas.exceptions import Unrecognized
from canvas.json_io import json_serializer, json_deserializer, \
	serialize_json, deserialize_json, serialize_datetime
from canvas.core.request_parsers import parse_datetime

@cvt.test('JSON API')
def test_json_api():
	#	Create a round-trippable class and conversion methods.
	class Foo:
		def __eq__(self, other):
			return isinstance(other, Foo)
	@json_serializer(Foo)
	def serialize_foo(foo):
		return '!foo'
	@json_deserializer
	def deserialize_foo(rep):
		if rep != '!foo':
			raise Unrecognized()
		return Foo()
	
	#	Create an input dict.
	some_time = datetime.now()
	input_dict = {
		'datetime': some_time,
		'number': 1,
		'string': 'foobar',
		'foo': Foo()
	}
	#	Round trip it.
	output_dict = deserialize_json(serialize_json(input_dict))

	#	Assert all expected behavior occurred.
	with cvt.assertion('Round trip identities all types'):
		for key, value in input_dict.items():
			check = output_dict[key]
			if isinstance(value, datetime):
				check = parse_datetime(check)
				assert serialize_datetime(value) == serialize_datetime(check)
			else:
				assert value == output_dict[key]
