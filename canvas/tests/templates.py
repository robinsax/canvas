#	coding utf-8
'''
Unit tests on the `CanvasJinjaEnvironment` and
its components.
'''

import os
import re

from .. import CANVAS_HOME
from . import *

@test('CanvasJinjaEnvironment')
def test_canvas_jinja_env():
	from ..core.assets.jinja_extensions import CanvasJinjaEnvironment

	base_paths = []
	for i in range(1, 4):
		base_paths.append(os.path.join(CANVAS_HOME, 'canvas', 'tests', 'extras', 'rendering', str(i), 'templates'))

	env = CanvasJinjaEnvironment(base_paths)
	
	def cleaned_render(file):
		return re.sub('\s+', ' ', env.get_template(file).render()).strip()

	basic_render = cleaned_render('basic.jinja')
	check((
		basic_render == 'Hello! Hello! Hello!'
	), 'Basic rendering')

	overlay_render = cleaned_render('override.jinja')
	check((
		overlay_render == 'One! Two! Three!'
	), 'Overlay rendering')
