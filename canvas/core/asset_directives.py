#	coding utf-8
'''
Asset directives.
'''

import os
import re

from ..exceptions import AssetError
from .plugins import get_path_occurrences

def apply_directives(source):
	for include_directive in re.finditer(r'//\s+cv::include\s+(.+)\s*?\n', source):
		include = '%s.jsx'%include_directive.group(1).strip()

		occurrences = get_path_occurrences('assets', 'client', include)
		if len(occurrences) == 0:
			raise AssetError('Bad include directive: %s'%include)
		
		with open(occurrences[0], 'r') as include_file:
			include_source = include_file.read()

		source = source.replace(include_directive.group(0), include_source + '\n')

	return source
