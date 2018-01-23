#   coding utf-8
'''
Code documentation generation.
'''

import os
import re
import inspect

#	Import the root package for reference.
import canvas

__all__ = [
	'build_docs'
]

#	The list of package paths to document. Due
#	to namespace management, the majority of relevant
#	code is imported these packages.
PACKAGES = [
	canvas,
	canvas.model,
	canvas.controllers
]

def class_doc(cls):
	#	Get doc. string.
	doc_str = cls.__doc__
	if doc_str is None:
		doc_str = '*No documentation*'

	mthd_doc_str = ''
	for name, mthd in inspect.getmembers(cls, predicate=inspect.isfunction):
		mthd_doc_str += f'{function_doc(mthd)}\n'
	
	return f'### {cls.__name__}({cls.__bases__[0].__name__})\n{inspect.cleandoc(doc_str)}\n#### Methods\n{mthd_doc_str}\n'

def function_doc(func):
	return f'### {func.__name__}\n'

def build_docs():
	'''
	Generate a Markdown file for each package in
	`PACKAGES` within the `./docs/code` directory.
	'''
	for package in PACKAGES:
		markdown = f'# {package.__name__}\n'

		#	Sort contents.
		classes, functions = [], []
		for attr in dir(package):
			attr = getattr(package, attr)

			if inspect.isclass(attr):
				classes.append(attr)
			elif inspect.isfunction(attr):
				functions.append(attr)

		#	Document.
		markdown += f'\n## Classes\n'
		for cls in classes:
			markdown += class_doc(cls)
		markdown += f'\n## Functions\n'
		for func in functions:
			markdown += function_doc(func)

		#	Save.
		with open(f'./docs/code/{package.__name__}.md', 'w') as f:
			f.write(markdown)
	
