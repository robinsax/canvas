#   coding utf-8
'''
Create a plugin template.

Must be invoked from the root directory.
'''

import os
import sys
import json
import shutil

USAGE = 'Usage: python3.6 ./scripts/create_plugin_template.py plugin_name'

def create_plugin_template(plugin_name):
	#	Load target directory from config or fail.
	if not os.path.isfile('settings.json'):
		print('No settings.json')
		sys.exit(1)
	with open('settings.json') as f:
		target_dir = json.load(f)['plugins']['directory']

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

	#	Copy .gitignore template.
	shutil.copyfile('./docs/templates/plugin.gitignore', f'{root}/.gitignore')

	#	Create assets folder.
	os.mkdir(f'{root}/assets')

	print('Done')

if __name__ == '__main__':
	if len(sys.argv) < 2:
		print(USAGE)
		sys.exit(1)
	create_plugin_template(sys.argv[1])
