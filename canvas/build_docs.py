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
	return None if obj.__doc__ is None else inspect.cleandoc(obj.__doc__.replace('TODO', '__TODO__'))

def class_doc(cls):
	#	Get doc. string.
	doc_str = get_doc_str(cls)
	if doc_str is None or re.match(r'_[A-Z]', cls.__name__):
		return None

	mthd_docs = []
	for name, mthd in inspect.getmembers(cls, predicate=inspect.isfunction):
		f_doc = function_doc(mthd, small=True)
		if f_doc is None:
			continue
		mthd_docs.append(f_doc)
	mthd_docs = '\n'.join(mthd_docs)
	
	doc = f'### {cls.__name__}({cls.__bases__[0].__name__})\n{doc_str}\n'
	if len(mthd_docs) > 0:
		doc += f'#### Methods\n{mthd_docs}\n'
	return doc

def function_doc(func, small=False):
	#	Get and process parameters from doc
	#	string.
	doc_str = get_doc_str(func)
	if doc_str is None or re.match(r'_[a-z]', func.__name__):
		return None

	arg_descs = []
	for match in re.finditer(r':(\w+)(\s[^:]+)', doc_str):
		doc_str = doc_str.replace(match.group(0), '')
		cleaned = re.sub(r'\s+', ' ', match.group(2))
		arg_descs.append(f'+ *{match.group(1)}*: {cleaned}')
	arg_descs = '\n'.join(arg_descs) + '\n'

	arg_spec = inspect.getfullargspec(func)
	arg_fmt = ''

	if arg_spec.args is not None:
		arg_fmt += ', '.join(arg_spec.args)

	if len(arg_spec.kwonlyargs) > 0:
		kwargs_strs = []
		for kwarg in arg_spec.kwonlyargs:
			kwargs_strs.append(f'{kwarg}={arg_spec.kwonlydefaults[kwarg]}')
		kwargs_str = ', '.join(kwargs_strs)
		if len(arg_fmt) > 0:
			arg_fmt += f', {kwargs_str}'
		else:
			arg_fmt = kwargs_str

	prefix = '#### ' if small else '### '

	func_name = func.__name__
	if func_name.startswith('__'):
		func_name = f'\\_\\_{func_name[2:]}'

	return f'{prefix}{func_name}({arg_fmt})\n{arg_descs}\n{doc_str}\n'

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
			c_doc = class_doc(cls)
			if c_doc is None:
				continue
			markdown += c_doc
		markdown += f'\n## Functions\n'
		for func in functions:
			f_doc = function_doc(func)
			if f_doc is None:
				continue
			markdown += f_doc

		#	Save.
		with open(f'./docs/code/{package.__name__}.md', 'w') as f:
			f.write(markdown)
	
