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

def get_doc_str(obj):
	return '*No documentation*' if obj.__doc__ is None else inspect.cleandoc(obj.__doc__)

def class_doc(cls):
	#	Get doc. string.
	doc_str = get_doc_str(cls)

	mthd_doc_str = ''
	for name, mthd in inspect.getmembers(cls, predicate=inspect.isfunction):
		mthd_doc_str += f'{function_doc(mthd)}\n'
	
	return f'### {cls.__name__}({cls.__bases__[0].__name__})\n{doc_str}\n#### Methods\n{mthd_doc_str}\n'

def function_doc(func):
	doc_str = get_doc_str(func)

	arg_spec = inspect.getfullargspec(func)
	arg_fmt = ''

	if arg_spec.args is not None:
		arg_fmt += ', '.join(arg_spec.args)

	if arg_spec.varkw is not None:
		kwargs_strs = []
		for i, kwarg in enumerate(arg_spec.kwonlyargs):
			print(func, kwarg)
			kwargs_strs.append(f'{kwarg}={arg_spec.kwonlydefaults[i]}')
		kwargs_str = ', '.join(kwargs_strs)
		if len(arg_fmt) > 0:
			arg_fmt += f', {kwargs_str}'
		else:
			arg_fmt = kwargs_str

	return f'### {func.__name__}({arg_fmt})\n{doc_str}\n'

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
	
