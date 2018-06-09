from enum import Enum

class TagType(Enum):
	NORMAL = 1
	SELF_CLOSING = 2
	UNCLOSED = 3

	@classmethod
	def guess(cls, name):
		if name in ('link',):
			return TagType.SELF_CLOSING
		if name in ('meta',):
			return TagType.UNCLOSED
		return TagType.NORMAL

class Tag:

	def __init__(self, name, *items, text=None, typ=None):
		self.name, self.type = name, typ if typ else TagType.guess(name)
		self.text = text

		self.attributes, self.children = None, list()
		for item in items:
			if isinstance(item, dict):
				self.attributes = item
			else:
				self.children.append(item)

	def render(self, depth=0):
		tabs, nl = ('\t'*depth, '\n')
		if self.text:
			return ''.join((tabs, '<', self.name, '>', self.text, '</', self.name, '>', nl))

		if self.attributes:
			attrs = ' ' + ' '.join(
				'%s="%s"'%tpl for tpl in self.attributes.items()
			)
		else:
			attrs = str()
		
		rep = ''.join((tabs, '<', self.name, attrs, '/>' if self.type is TagType.SELF_CLOSING else '>', nl))
		if self.type is TagType.NORMAL:
			rep = ''.join((
				rep,
					*((child if isinstance(child, str) else child.render(depth + 1)) for child in self.children),
				tabs, '</', self.name, '>', nl
			))
		return rep

class TagFactory:

	def __getattr__(self, key):
		def create_tag(*items, **kwargs):
			return Tag(key, *items, **kwargs)
		return create_tag

tf = TagFactory()
def f(debug, route, title, description):
	return tf.html(
		tf.head({'data-debug': debug, 'data-route': route},
			tf.meta({'charset': 'utf-8'}),
			tf.meta({'name': 'viewport', 'content': 'width=device-width, initial-scale=1'}),
			tf.title(text=title),
			tf.meta({'name': 'description', 'content': description}),
			tf.link({'rel': 'icon', 'type': 'image/png', 'href': '/media/site_icon.png'}),
			tf.script({'type': 'text/javascript'}, text='TODO Model Defns')
		)
	)
print(f('true', '/test', 'Foo', 'Foobar').render())