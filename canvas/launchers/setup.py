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

@launcher('config', {
	'argspec': '<key=value, ...>',
	'description': 'Apply a set of key, value configuration pairs. Key levels are delimited with ".". List values are joined with ",".'
})
def launch_configuration(args):
	with open(os.path.join(__home__, 'settings.json')) as config_file:
		raw_config = json.load(config_file)
	
	try:
		for item in args:
			key, value = item.split('=')
			if ',' in value:
				value = [s for s in value.split(',') if len(s.strip()) > 0]
			levels = key.split('.')
			current = raw_config
			for level in levels[:-1]:
				current = current[level]
			current[levels[-1]] = value
	except:
		return False

	to_write = json.dumps(raw_config, indent=4).replace('    ', '\t')
	with open(os.path.join(__home__, 'settings.json'), 'w') as config_file:
		config_file.write(to_write)
	
	print('Wrote %d entries'%len(args))
	return True

@launcher('init-db', {
	'description': '''Initialize the database (must be run as a user with 
		configured peer-authentication).'''
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
	
	return True
	