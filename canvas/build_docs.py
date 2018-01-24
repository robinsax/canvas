#   coding utf-8
'''
Code documentation generation.
'''

import os
import re
import inspect

#	TODO: Create plugin interface.
#	TODO: Only document things in the module in which
#		they were defined.

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

	if arg_spec.defaults is None:
		arg_fmts = arg_spec.args
		kw_args = arg_spec.kwonlyargs
		kw_defaults = arg_spec.kwonlydefaults
	else:
		arg_fmts = arg_spec.args[0:-len(arg_spec.defaults)]
		kw_args = arg_spec.args[len(arg_fmts):]
		kw_defaults = {}
		for i, arg in enumerate(kw_args):
			kw_defaults[arg] = arg_spec.defaults[i]

	if arg_spec.varargs is not None:
		arg_fmts.append(f'*{arg_spec.varargs}')
	
	#	Keywords
	for arg in kw_args:
		arg_fmts.append(f'{arg}={kw_defaults[arg]}')

	arg_fmt = ', '.join(arg_fmts)

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
	
