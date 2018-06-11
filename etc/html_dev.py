# coding: pyxl
'''
Native views are PYX-enabled views useful for rendering static pages. Source
files containing native views must declare a `pyxl` encoding and use spaces
for indentation.
'''

from pyxl import html
from pyxl.element import x_element

class View(x_element):

    def __init__(self, data=None):
        self.data = data

    def render(self):
        return self.__class__.__template__(self.data)

def view(template=None):
    def view_wrap(cls):
        cls = type(cls.__name__, (cls, View), dict())
        cls.__template__ = template
        return cls
    return view_wrap

@view(
	template=lambda data: (
		<html>
			<head>
				<meta charset="utf-8"/>
				<meta name="viewport" content="width=device-width, initial-scale=1"/>
				<meta name="description" content="TODO"/>
				<title>{ data }</title>
			</head>
			<body>
				<header class="header">
				</header>
				<div class="page">
				</div>
				<footer class="footer">
				</footer>
			</body>
		</html>
	)
)
class PageView: pass

print(PageView('Test page').render())