#	coding utf-8
'''
Setup and configuration.
'''

import os
import pip
import sys
import json
import shutil

from subprocess import Popen, PIPE

from ..utils import format_exception
from .. import __home__
from . import launcher

def fail():
	print('Failed')
	sys.exit(1)

class step:
	def __init__(self, label):
		self.label = label

	def __enter__(self):
		print(self.label)

	def __exit__(self, type, value, traceback):
		if traceback and not isinstance(value, SystemExit):
			print(format_exception(value))
			fail()
		else:
			print('Done')

@launcher('init', {
	'description': "Install canvas's dependencies and create its configuration"
})
def launch_setup(args):
	with step('Installing Python requirements...'):
		with open(os.path.join(__home__, 'requirements.txt'), 'r') as req_file:
			requirements = req_file.readlines()
		
		exit_code = pip.main(['install'] + [
			l.strip() for l in requirements if not l.startswith('#')
		])
		if exit_code > 0:
			fail()

	with step('Installing Node requirements...'):
		with open(os.path.join(__home__, 'required_packages'), 'r') as pkg_file:
			packages = pkg_file.readlines()

		proc = Popen(' '.join(['npm', 'install'] + [p.strip() for p in packages]), 
			shell=True, 
			stdout=PIPE, 
			stderr=PIPE
		)

		out, err = proc.communicate()
		print(out.decode().strip())
		if proc.returncode > 0:
			print(err.decode().strip())
			fail()

	with step('Creating configuration...'):
		shutil.copyfile(
			os.path.join(__home__, 'default_settings.json'), 
			os.path.join(__home__, 'settings.json')
		)

	return True

@launcher('apply-config', {
	'description': 'Perform all setup dependent on configuration state'
})
def launch_apply_config(args):
	from ..configuration import load_config, config
	load_config()

	with step('Setting up Postgres...'):
		psql_input = '\n'.join([
			'CREATE USER %s;'%config.database.user,
			'CREATE DATABASE %s;'%config.database.database,
			"ALTER USER %s WITH PASSWORD '%s';"%(
				config.database.user, 
				config.database.password
			),
			'GRANT ALL ON DATABASE %s TO %s;'%(
				config.database.database,
				config.database.user
			),
			'\q\n'
		])
		proc = Popen('psql --username=postgres --password', shell=True,
			stdin=PIPE, 
			stdout=PIPE,
			stderr=PIPE
		)

		out, err = proc.communicate(psql_input.encode())
		print(out.decode().strip())
		if len(err) > 0:
			print(err.decode().strip())
			fail()

	with step('Creating plugin folder...'):
		path = os.path.join(__home__, config.plugins.directory)
		if not os.path.exists(path):
			os.mkdir(path)

	return True
	