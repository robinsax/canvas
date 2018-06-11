# coding: utf-8
'''
The HTML page creation API. The recommended pattern is to minimize server-side
page content generation, serving pages that contain the information required
by search engines and other crawlers, with assets that will generate the
page itself.
'''

from ...exceptions import InvalidAsset
from ...configuration import config
from .tags import TagType, Tag, tag_factory as tf

class Page:

	def __init__(self, route, title, description=None, assets=tuple(), 
			models=tuple()):
		self.route, self.title = route, title
		self.description = description
		self.assets = assets

	def head(self):
		#	Tagify the asset list.
		asset_tags = list()
		for asset in (*config.customization.global_assets, *self.assets):
			route = '/'.join((config.customization.asset_route_prefix, asset))
			if asset.endswith('.css'):
				asset_tags.append(
					tf.link({
						'rel': 'stylesheet', 'type': 'text/css',
						'href': route 
					})
				)
			elif asset.endswith('.js'):
				asset_tags.append(
					tf.script({
						'type': 'text/javascript',
						'src': route,
						'defer': 'true'
					})
				)
			else:
				raise InvalidAsset(asset)

		return <head></head>

		return tf.head({
			'data-debug': config.development.debug, 
			'data-route': self.route
		},
			tf.meta({'charset': 'utf-8'}),
			tf.meta({
				'name': 'viewport', 
				'content': 'width=device-width, initial-scale=1'
			}),
			tf.title(text=self.title),
			tf.meta({
				'name': 'description', 
				'content': self.description if self.description else str()
			}),
			tf.link({
				'rel': 'icon', 'type': 'image/png', 
				'href': '/media/site_icon.png'
			}),
			*self.head_extras(),
			tf.script({'type': 'text/javascript'}, text='TODO Model Defns'),
			*asset_tags
		)

	def head_extras(self):
		return tuple()

	def body(self):
		return tf.body({
			'data-route': self.route
		},
			tf.header({'class': 'header'}),
			tf.div({'class': 'body'}),
			tf.footer({'class': 'footer'})
		)

	def create(self):
		return tf.html(
			self.head(),
			self.body()
		)
