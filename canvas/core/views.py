# coding: pyxl
'''
Native views are PYX-based views used for rendering static pages. Source
files containing native views must declare a `pyxl` encoding and use spaces
for indentation. Usage of this interface should be minimized as it is
unstable.
'''

from pyxl import html
from pyxl.element import x_element

from ..exceptions import InvalidAsset
from ..dictionaries import AttributedDict

class View(x_element):
	'''The root view class.'''

	def set_data(self, data):
		self.__data__ = data

    def render(self):
        return self.__class__.__template__(self.__data__)

def view(*, template=None):
	'''The view registration decorator.'''
    def view_inner(cls):
        cls = type(cls.__name__, (cls, View), dict())
        cls.__template__ = template
        return cls
    return view_inner

@view(
	template=lambda data: (
		<html>
			<head>
				<meta charset="utf-8"/>
				<meta name="viewport" content="width=device-width, initial-scale=1"/>
				<meta name="description" content={ data.description if data.description else "This page has no description." }/>
				<title>{ data }</title>
				{ *data.assets }
			</head>
			<body>
				<header class="header">{ *data.header_views }</header>
				<div class="page">{ *data.page_views }</div>
				<footer class="footer">{ *data.footer_views }</footer>
			</body>
		</html>
	)
)
class PageView:

	def __init__(self, title, description, assets, models, header_views=list(), page_views=list(), footer_views=list()):
		self.set_data(AttributedDict(
			title=title,
			description=description,
			assets=self.process_assets(assets),
			models=self.process_models(models),
			header_views=header_views,
			page_views=page_views,
			footer_views=footer_views
		))

	def process_assets(self, assets):
		asset_tags = list()
		for asset in assets:
			if asset.endswith('.css'):
				asset_tags.append(<link rel="stylesheet" type="text/css" href=asset/>)
			elif asset.endswith('.js'):
				asset_tags.append(<script type="text/javascript" src=asset/>)
			else:
				raise InvalidAsset(asset)
		return asset_tags
	
	def process_models(self, models):
		return models

@cv.view(
	template=lambda error: (
		<div class="align-center vertical-center">
			<div>
				<h2 class="align-left">{ ' '.join(error.code, error.title) }</h2>
				<p class="align-right">Sorry about that!</p>
				<if cond={ error.debug_info }>
					<div class="align-left">
						<h4>Traceback</h4>
						<code><pre>{ error.debug_info.traceback }</pre></code>
						<h4>Context</h4>
						<code><pre>{ error.debug_info.context }</pre></code>
					</div>
				</if>
			</div>
		</div>
	)
)
class ErrorView: pass
