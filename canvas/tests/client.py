#   coding utf-8
'''
An extension of the werkzeug testing client.
'''

from werkzeug.test import Client
from werkzeug.wrappers import BaseResponse

from ..core.json_io import serialize_json, deserialize_json
from .. import application
from . import Failure

class CanvasTestClient(Client):

	def __init__(self):
		super().__init__(application, BaseResponse)

	def get_json(self, url):
		response = self.get(url)
		response.json = deserialize_json(response.data.decode())
		response.ok = response.status_code == 200
		return response

	def put_json(self, url, content_type=None, json=None):
		if json:
			content_type = 'application/json'
			json = serialize_json(json)
		response = self.put(url, content_type=content_type, data=json)
		response.json = deserialize_json(response.data.decode())
		response.ok = response.status_code == 200
		return response

	def post_json(self, url, content_type=None, json=None):
		if json:
			content_type = 'application/json'
			json = serialize_json(json)
		response = self.post(url, content_type=content_type, data=json)
		response.json = deserialize_json(response.data.decode())
		response.ok = response.status_code == 200
		return response
