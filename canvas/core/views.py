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
from ..utils import create_callback_registrar
from ..dictionaries import AttributedDict

#	Define the page view definition callback, used to override the root page 
#	view.
on_page_view_defined = create_callback_registrar(loop_arg=True)

class View(x_element):
	'''
	The root view class. Overriding in redundant as the `view` decorator causes
	it to occur implicitly
	'''

    def render(self):
		'''Return a snippet of HTML.'''
        raise NotImplementedError()

def view(_=None):
	'''The view registration decorator.'''
	def inner_view(cls):
		return type(cls.__name__, (cls, View), dict())
	return inner_view

@view()
class PageView:
	'''
	The base view used to render pages. To override or extend, register an 
	`on_page_view_defined` callback that accepts this class or a subclass of it
	and returns a further subclass.
	'''
	#	Used to store the plugin-modified version of this class.
	resolved_class = None

	def __init__(self, title, description=None, assets=tuple()):
		'''
		Configure an overriding page view. Overrides of this class must have
		the same argument specification.
		'''
		self.title, self.description = title, description
		self.assets = assets
		self.header_views, self.page_views, self.footer_views = list(), /
				list(), list()
		
	@classmethod
	def resolved(cls):
		'''Return the plugin-modified version of this class.'''
		if not PageView.resolved_class:
			PageView.resolved_class = on_page_view_defined.invoke(PageView)
		return PageView.resolved_class

	def meta_fragment(self):
		'''Return the metadata fragment of the page.'''
		description = data.description
		if not description:
			description = "This page has no description."
		return <frag>
			<meta charset="utf-8"/>
			<meta name="viewport" content="width=device-width, initial-scale=1"/>
			<meta name="description" content={ description }/>
		</frag>

	def asset_fragement(self):
		'''Return the asset inclusion fragement of this page.'''
		asset_tags = list()
		for asset in self.assets:
			if asset.endswith('.css'):
				asset_tags.append(<link rel="stylesheet" type="text/css" href=asset/>)
			elif asset.endswith('.js'):
				asset_tags.append(<script type="text/javascript" src=asset/>)
			else:
				raise InvalidAsset(asset)
		return <frag>{ *asset_tags }</frag>

	def render(self):
		'''
		Return the HTML document itself. The `DOCTYPE` declaration is handled by the `Page`.
		'''
		return <html>
			<head>
				{ self.meta_fragment() }
				<title>{ data }</title>
				{ *self.asset_fragement() }
			</head>
			<body>
				<header class="header">{ *data.header_views }</header>
				<div class="page">{ *data.page_views }</div>
				<footer class="footer">{ *data.footer_views }</footer>
			</body>
		</html>

@view()
class ErrorView:
	'''
	A view used to render the default error screen, with debug information if
	applicable.
	'''

	def __init__(self, error):
		'''::error The `HTTPException` that occurred.'''
		self.error = error

	def render(self):
		return <div class="align-center vertical-center">
			<div>
				<h2 class="align-left">{ ' '.join(self.error.code, self.error.title) }</h2>
				<p class="align-right">Sorry about that!</p>
				<if cond={ self.error.debug_info }>
					<div class="align-left">
						<h4>Traceback</h4>
						<code><pre>{ self.error.debug_info.traceback }</pre></code>
						<h4>Context</h4>
						<code><pre>{ self.error.debug_info.context }</pre></code>
					</div>
				</if>
			</div>
		</div>
