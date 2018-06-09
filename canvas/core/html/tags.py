#	coding utf-8
'''
HTML generation and rendering utilities.
'''

from enum import Enum

from ...exceptions import InvalidTag

class TagType(Enum):
	'''An enumerable type of tag variants.'''
	NORMAL =		1	# A standard tag.
	SELF_CLOSING =	2	# A self closing tag.
	UNCLOSED =		3	# An unclosed tag (why do these exist??).

	@classmethod
	def guess(cls, name):
		'''Guess the type of a tag given its name.'''
		if name in ('link', 'img', 'input'):
			return TagType.SELF_CLOSING
		if name in ('meta',):
			return TagType.UNCLOSED
		return TagType.NORMAL

class Tag:
	'''An HTML tag with a name, attributes, and children.'''

	def __init__(self, name, *items, text=None, typ=None):
		'''
		Create a new tag.
		::name The tag name.
		::items Children `Tag`s. The first item may be a dictionary containing
			the attributes of this tag.
		::text The leading text of this tag.
		::typ The `TagType` of this tag.
		'''
		self.name, self.text = name, text
		#	Guess the type if it wasn't provided.
		self.type = typ if typ else TagType.guess(name)

		#	Parse the supplied items.
		self.attributes, self.children = None, list()
		for item in items:
			if isinstance(item, dict):
				self.attributes = item
			else:
				self.children.append(item)

		#	Inspect contents.
		self.has_tag_children = False
		for child in self.children:
			if isinstance(child, Tag):
				self.has_tag_children = True
				break

		#	Assert this is a valid tag.
		if self.children or self.text and not self.type == TagType.NORMAL:
			raise InvalidTag('Irregular tags cannot have')

	def render(self, depth=0):
		'''Render this tag and its children as a string.'''
		#	Define the tab string and newline.
		tabs, newline = '\t'*depth, '\n'

		#	Render the attributes.
		if self.attributes:
			attrs = ' ' + ' '.join(
				'%s="%s"'%tpl for tpl in self.attributes.items()
			)
		else:
			attrs = str()

		#	Render a single child.
		def render_child(child):
			if isinstance(child, Tag):
				return child.render(depth + 1)
			return child
		
		#	Render opening tag.
		html = ''.join((
			tabs, '<', self.name, attrs, 
			'/>' if self.type is TagType.SELF_CLOSING else '>', 
			newline
		))
		if self.text:
			#	Render head text.
			html = ''.join((html, self.text))
		if self.type is TagType.NORMAL:
			#	Render children and closing tag.
			html = ''.join((
				html,*(render_child(child) for child in self.children),
				tabs if self.has_tag_children else str(), '</', self.name, '>',
				newline
			))
		return html

class TagFactory:
	'''
	A helper class that improves tag-creation syntax by allowing the following
	usage:
	```
	tf = TagFactory()
	tag = tf.div({'class': 'my-div'})
	```
	'''

	def __getattr__(self, key):
		def create_tag(*items, **kwargs):
			return Tag(key, *items, **kwargs)
		return create_tag