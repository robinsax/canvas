#   coding utf-8
'''
Plugin template generation.
'''

import os
import sys
import shutil

from .. import config
from . import logger

#   Declare exports.
__all__ = [
    'create_plugin_template'
]

log = logger()

def create_plugin_template(plugin_name):
	#	Load target directory from config or fail.
	target_dir = config['plugins']['directory']

	def detemplate(string, variables):
		'''
		Detemplate all variables in `variables` within
		`string`.
		'''
		for name, value in variables.items():
			string = string.replace(f'${name}', value)

		return string
	
	def detemplate_file_to(src, dest, variables):
		'''
		Load and detemplate `src`, then write
		to `dest`
		'''
		with open(src, 'r') as src_f, open(dest, 'w') as dest_f:
			dest_f.write(detemplate(src_f.read(), variables))

	#	Create the root directory.
	root = f'{target_dir}/canvas-pl-{plugin_name}'
	os.makedirs(root)

	#   De-template and copy settings.
	detemplate_file_to('./docs/templates/plugin_settings.json', f'{root}/settings.json', {
		'plugin_name': plugin_name
	})

	#	De-template and copy Travis YML
	detemplate_file_to('./docs/templates/plugin_travis.yml', f'{root}/.travis.yml', {
		'plugin_name': plugin_name,
		'test_suite_names': plugin_name
	})

	#	Create package...
	pkg_root = f'{root}/{plugin_name}'
	os.mkdir(pkg_root)
	#	...and __init__.py
	detemplate_file_to('./docs/templates/plugin_init.py', f'{pkg_root}/__init__.py', {
		'plugin_name': plugin_name
	})

	#	Create test package...
	pkg_root = f'{root}/tests'
	os.mkdir(pkg_root)
	#	...and __init__.py
	detemplate_file_to('./docs/templates/plugin_test_init.py', f'{pkg_root}/__init__.py', {
		'plugin_name': plugin_name
	})

	#	Copy non-template.
	shutil.copyfile('./docs/templates/plugin.gitignore', f'{root}/.gitignore')
	shutil.copyfile('./docs/templates/plugin_dependencies.txt', f'{root}/dependencies.txt')
	shutil.copyfile('./docs/templates/plugin_requirements.txt', f'{root}/requirements.txt')
	shutil.copyfile('./docs/templates/plugin_coveragerc', f'{root}/.coveragerc')

	#	Create assets folder.
	os.mkdir(f'{root}/assets')
	#	Create documentation folder.
	os.mkdir(f'{root}/docs')
	os.mkdir(f'{root}/docs/code')

	log.info(f'Created plugin {plugin_name} in {root}')
