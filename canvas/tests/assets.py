#	coding utf-8
'''
Unit tests on the `CanvasJinjaEnvironment` and
its components.
'''

import os
import re

from .. import CANVAS_HOME
from . import *

assets_test = TestSuite('canvas.core.assets')

@assets_test('Jinja environment')
def test_jinja_environ():
	'''
	Unit tests on the CanvasJinjaEnvironment object.

	TODO: Create test for markdown_file() helper.
	'''
	from ..exceptions import MacroParameterError
	from ..utils.registration import register
	from ..core.assets.jinja_extensions import CanvasJinjaEnvironment
	from .. import config

	#	Create a fake set of base paths from `./extras`.
	base_paths = []
	for i in range(1, 4):
		base_paths.append(os.path.join(CANVAS_HOME, 'canvas', 'tests', 'test_assets', 'rendering', str(i), 'templates'))

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

	#	Case: template helper and filter implementations.
	case('Template utilities')

	#	Check utility filters.
	filter_render = cleaned_render('util_filter_check.jinja')
	check((
		filter_render == '<h1>Foobar</h1> '*2 + '{"foo": "bar"} %40'
	), 'Template filters')

	check_throw(lambda: cleaned_render('throw_check.jinja'), 
			MacroParameterError, 'parameter_error() helper')

	#	*Note:* core filters are checked with model since they depend on it.

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
