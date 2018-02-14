#   coding utf-8
'''
Build the frontend into `canvas/assets/client`.
'''

import re
import sys
import requests

MINIFY_ENDPOINT = 'https://javascript-minifier.com/raw'
HEADER = '''/*
	The canvas core.

	Author: Robin Saxifrage
	License: Apache 2.0
*/
'''

def main():
	dev_mode = len(sys.argv) > 1 and sys.argv[1] == '--dev'

	def collect_file(filename):
		with open(f'./frontend_src/{filename}') as f:
			source = f.read()

		for match in re.finditer(r'(\t+)\/\*\s+::include\s+(.*?)\s+\*\/', source):
			subsource = collect_file(match.group(2))
			subsource = subsource.replace('\n', f'\n{match.group(1)}')
			source = source.replace(match.group(0), f'{match.group(1)}{subsource}')

		return source

	source = collect_file('core.js')
	if not dev_mode:
		response = requests.post(MINIFY_ENDPOINT, data={
			'input': source
		}).text

		error = list(re.finditer(r'\/\/\s+Line\s+:\s+([0-9]+)', response))
		if len(error) > 0:
			lines = source.split('\n')
			line = int(error[0].group(1))
			bottom, top = max(0, line-1), min(len(lines), line+10)
			print(response)
			print('\n'.join(lines[bottom:top]))
			sys.exit(1)
		
		source = response
	
	with open('canvas/assets/templates/client/core.min.js', 'w') as f:
		f.write(f'{HEADER}{source}')

if __name__ == '__main__':
	main()
