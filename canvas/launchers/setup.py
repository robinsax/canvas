#	coding utf-8
'''
Setup and configuration.
'''

import os
import pip
import sys

from subprocess import Popen, PIPE

from ..core.json_io import deserialize_json, serialize_json
from ..utils import format_exception
from .. import __home__
from . import launcher

@launcher('setup', {
	'description': "Install canvas's dependencies and run through configuration"
})
def launch_setup(args):
	def fail():
		print('Failed')
		sys.exit(1)

	class step:
		def __init__(self, label):
			self.label = label

		def __enter__(self):
			print(self.label)

		def __exit__(self, type, value, traceback):
			if traceback:
				print(format_exception(traceback))
				fail()
			else:
				print('Done')


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

		proc = Popen(['npm', 'install', '-g'] + packages, shell=True, stdout=PIPE, stderr=PIPE)
		out, err = proc.communicate()
		print(out.decode().strip())
		if proc.returncode > 0:
			print(err)
			fail()

	with step('Creating configuration...'):
		with open(os.path.join(__home__, 'default_settings.json'), 'r') as config_file:
			config = deserialize_json(config_file.read())

	return True