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
from ..configuration import config
from ..dictionaries import AttributedDict
from .request_context import RequestContext

#    Define the page view alteration callback, used to override the root page 
#    view.
alter_root_page_view = create_callback_registrar(loop_arg=True)

class View:
    '''
    The root view class. Overriding is redundant as the `view` decorator causes
    it to occur implicitly.
    '''

    def render(self):
        '''Return a snippet of HTML.'''
        raise NotImplementedError()

    def __str__(self):
        return str(self.render())

def view(_=None):
    '''The view registration decorator.'''
    def inner_view(cls):
        return type(cls.__name__, (cls, View), dict())
    return inner_view

@view()
class PageView:
    '''
    The base view used to render pages. To override or extend, register an 
    `alter_root_page_view` callback that accepts this class or a subclass of it
    and returns a further subclass.
    '''
    #    Used to store the plugin-modified version of this class.
    resolved_class = None

    def __init__(self, title, description=None, assets=tuple()):
        '''
        Configure an overriding page view. Overrides of this class must have
        the same argument specification.
        '''
        self.title, self.description = title, description
        self.assets = ('canvas.css', 'canvas.js', *assets)
        self.header_views, self.page_views, self.footer_views = list(), \
                list(), list()
        
    @classmethod
    def resolved(cls, *args, **kwargs):
        '''Return the plugin-modified version of this class.'''
        if not PageView.resolved_class:
            PageView.resolved_class = alter_root_page_view.invoke(PageView)
        return PageView.resolved_class(*args, **kwargs)

    def meta_fragment(self):
        '''Return the metadata fragment of the page.'''
        description = self.description
        if not description:
            description = "This page has no description."
        return <frag>
            <meta charset="utf-8"></meta>
            <meta name="viewport" content="width=device-width, initial-scale=1"></meta>
            <meta name="description" content={ description }></meta>
        </frag>

    def tagify_asset(self, route):
        '''Create a tag for the asset at `route`.'''
        #    Ensure route is asset prefixed.
        if not route.startswith(config.customization.asset_route_prefix):
            route = '/'.join((
                config.customization.asset_route_prefix, route
            ))
        
        if route.endswith('.css'):
            return <link rel="stylesheet" type="text/css" href={ route }></link>
        elif route.endswith('.js'):
            return <script type="text/javascript" src={ route }></script>
        else:
            raise InvalidAsset(route)

    def asset_fragement(self):
        '''Return the asset inclusion fragement of this page.'''
        asset_tags = (self.tagify_asset(asset) for asset in self.assets)
        return <frag>{ *asset_tags }</frag>

    def html_attributes(self, route):
        '''Return a dictionary of attributes for the root HTML tag.'''
        return dict()

    def head_attributes(self, route):
        '''Return a dictionary of attributes for the head tag.'''
        return {
            'data-debug': 'true' if config.development.debug else 'false',
            'data-route': route
        }
    
    def body_attributes(self, route):
        '''Return a dictionary of attributes for the body tag.'''
        return {
            'data-route': route
        }

    def render(self):
        '''
        Return the HTML document itself. The `DOCTYPE` declaration is handled 
        by the `Page`.
        '''
        request_context = RequestContext.get()
        route = request_context.route if request_context else None
        def render_views(views):
            return (html.rawhtml(view.render()) for view in views)

        head = <head>
            { self.meta_fragment() }
            <title>{ self.title }</title>
            { self.asset_fragement() }
        </head>
        for key, value in self.head_attributes(route).items():
            head.set_attr(key, value)
        
        body = <body>
            <header class="header">{ *render_views(self.header_views) }</header>
            <div class="page">{ *render_views(self.page_views) }</div>
            <footer class="footer">{ *render_views(self.footer_views) }</footer>
        </body>
        for key, value in self.body_attributes(route).items():
            body.set_attr(key, value)

        html_ = <html>
            { head }
            { body }
        </html>
        for key, value in self.html_attributes(route).items():
            html_.set_attr(key, value)

        return html_

@view()
class ErrorView:
    '''
    A view used to render the default error screen, with debug information if
    applicable.
    '''

    def __init__(self, error):
        '''::error The error dictionary from the exception.'''
        self.error = error

    def render(self):
        return <div class="align-center fill-parent">
            <div class="col-6 vertical-center">
                <h2 class="align-left">
                    { ' '.join((str(self.error['code']), self.error['title'])) }
                </h2>
                <p class="align-right">Sorry about that!</p>
                <if cond={ 'debug_info' in self.error }>
                    <div class="align-left">
                        <h4>Traceback</h4>
                        <pre><code>{ self.error['debug_info']['traceback'] }</code></pre>
                        <h4>Context</h4>
                        <pre><code>{ self.error['debug_info']['context'] }</code></pre>
                    </div>
                </if>
            </div>
        </div>
