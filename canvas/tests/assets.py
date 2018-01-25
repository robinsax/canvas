#	coding utf-8
'''
Unit tests on the `CanvasJinjaEnvironment` and
its components.
'''

import os
import re

from .. import CANVAS_HOME
from . import *

assets_test = TestSuite('assets')

@assets_test('Jinja environment')
def test_jinja_environ():
	'''
	Unit tests on the CanvasJinjaEnvironment object.
	'''
	from ..utils.registration import register
	from ..core.assets.jinja_extensions import CanvasJinjaEnvironment
	from .. import config

	#	Create a fake set of base paths from `./extras`.
	base_paths = []
	for i in range(1, 4):
		base_paths.append(os.path.join(CANVAS_HOME, 'canvas', 'tests', 'extras', 'rendering', str(i), 'templates'))

	#	Create a simple helper and global to use in testing.
	@register.template_helper
	@register.template_global
	def fn():
		return 'foobar'

	env = CanvasJinjaEnvironment(base_paths)
	
	def cleaned_render(file):
		return re.sub('\s+', ' ', env.get_template(file).render()).strip()
	
	#	Test basic loading and rendering.
	basic_render = cleaned_render('basic.jinja')
	check((
		basic_render == 'Hello! Hello! Hello!'
	), 'Basic rendering')

	#	Test the `overlay` tag.
	overlay_render = cleaned_render('override.jinja')
	check((
		overlay_render == 'One! Two! Three!'
	), '{% overlay %}')

	#	Test the `page` tag.
	page_render = cleaned_render('pages/test_page.html')
	check((
		page_render == 'Base Page'
	), '{% page %}')

	#	Test the `component` tag.
	component_render = cleaned_render('components/test_component.html')
	check((
		component_render == 'Base Component'
	), '{% component %}')

	#	Test template helpers, globals, and config presence.
	presence_render = cleaned_render('presence_check.jinja')
	name = config['name']
	check((
		presence_render == f'{name} foobar foobar'
	), 'Template helpers, globals, and config presence')


@assets_test('less compilation')
def test_less_basic():
	'''
	Unit test on less definition insertion and compilation.
	'''
	from ..core.assets import compile_less

	subcase('Header validity')
	try:
		compile_less('''
			@media (max-width: @breakpoint_1){
				div {
					color: @base_background1;
				}
			}
		''')
	except:
		fail()
	
@assets_test('Markdown rendering')
def test_markdown_basic():
	'''
	Unit tests on markdown
	'''