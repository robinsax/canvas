# coding: utf-8
'''
Setup and configuration launch modes for easier installation.
'''

import os
import pip
import json
import shutil

from subprocess import Popen, PIPE

from ..utils import trying
from .. import __home__
from .api import launcher

@launcher('init',
	description="Install canvas's dependencies and create a configuration file"
)
def launch_setup(args):
	'''
	The installation launcher which installs canvas's Python and Node 
	dependencies.
	'''
	with trying('Installing Python requirements...'):
		#	Read the list of required packages.
		with open(os.path.join(__home__, 'requirements.txt'), 'r') as req_file:
			requirements = req_file.readlines()
		
		#	Run pip.
		exit_code = pip.main(['install', *(
			l.strip() for l in requirements if not l.startswith('#')
		)])
		if exit_code:
			trying.fail()

	with trying('Installing Node requirements...'):
		#	Read the list of required packages.
		with open(os.path.join(__home__, 'required_packages'), 'r') as pkg_file:
			packages = pkg_file.readlines()
		
		#	Run npm.
		npm_process = Popen(' '.join((
			'npm', 'install', *(p.strip() for p in packages
		))), shell=True, stdout=PIPE,  stderr=PIPE)
		out, err = npm_process.communicate()

		print(out.decode().strip())
		if proc.returncode:
			trying.fail(err.decode().strip())

	with trying('Creating configuration...'):
		#	Copy out the configuration file.
		shutil.copyfile(
			os.path.join(__home__, 'etc', 'default_settings.json'), 
			os.path.join(__home__, 'settings.json')
		)

	return True

@launcher('config',
	argspec='<key=value, ...>',
	description='Apply a set of key, value configuration pairs. Key levels are delimited with ".". List values are joined with ","'
)
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

@launcher('write-setup-sql',
	description='Output SQL which can be used to initialize the database.'
)
def launch_init_db(args):
	from ..configuration import load_config, config
	load_config()

	print('\n'.join([
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
	]))
	return True
