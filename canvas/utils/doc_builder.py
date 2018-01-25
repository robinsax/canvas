#   coding utf-8
'''
Code documentation generation.
'''

import os
import re
import sys
import inspect

#	Import the root package for reference.
import canvas

__all__ = [
	'build_docs'
]

def get_doc_str(obj):
	'''
	Return a cleaned and formatted documentation string for `obj`, or `None` 
	if `obj` doesn't have one.
	'''
	return None if obj.__doc__ is None else inspect.cleandoc(obj.__doc__.replace('TODO', '__TODO__'))

def class_doc(cls):
	'''
	Create markdown documentation for a class, including its methods or
	return `None` if the class is not a valid documentation target.

	:cls The class to document.
	'''
	#	Get the documentation string.
	doc_str = get_doc_str(cls)
	#	Assert the target is valid.
	if doc_str is None or re.match(r'_[A-Z]', cls.__name__):
		return None

	#	Collect method documentation.
	method_docs = []
	for name, method in inspect.getmembers(cls, predicate=inspect.isfunction):
		doc = function_doc(method, small=True)
		if doc is None:
			#	Invalid target.
			continue
		method_docs.append(doc)
	method_docs = '\n'.join(method_docs)
	
	#	Collect and return documentation markdown.
	doc = f'### {cls.__name__}({cls.__bases__[0].__name__})\n{doc_str}\n'
	if len(method_docs) > 0:
		doc += f'#### Methods\n{method_docs}\n'
	return doc

def function_doc(func, small=False):
	'''
	Create markdown documentation for a function or return `None` if the class
	is not a valid documentation target.

	:func The function to document.
	:small Whether the function title should be smaller than normal.
	'''
	#	Get the documentation string.
	doc_str = get_doc_str(func)
	#	Assert the target is valid.
	if doc_str is None or re.match(r'_[a-z]', func.__name__):
		return None

	#	Create the argument documentation.
	arg_descs = []
	for match in re.finditer(r':(\w+)(\s[^:]+)', doc_str):
		doc_str = doc_str.replace(match.group(0), '')
		cleaned = re.sub(r'\s+', ' ', match.group(2))
		arg_descs.append(f'+ *{match.group(1)}*: {cleaned}')
	arg_descs = '\n'.join(arg_descs) + '\n'

	#	Get the argument specification.
	arg_spec = inspect.getfullargspec(func)

	#	Handle the keyword-only versus optional positional argument cases.
	if arg_spec.defaults is None:
		#	Keyword only arguments.
		arg_fmts = arg_spec.args
		kw_args = arg_spec.kwonlyargs
		kw_defaults = arg_spec.kwonlydefaults
	else:
		#	Optional positional arguments.
		arg_fmts = arg_spec.args[0:-len(arg_spec.defaults)]
		kw_args = arg_spec.args[len(arg_fmts):]
		kw_defaults = {}
		for i, arg in enumerate(kw_args):
			kw_defaults[arg] = arg_spec.defaults[i]

	#	Add the optional variable arguments argument if present.
	if arg_spec.varargs is not None:
		arg_fmts.append(f'*{arg_spec.varargs}')
	
	#	Add keywords.
	for arg in kw_args:
		arg_fmts.append(f'{arg}={kw_defaults[arg]}')

	#	Join the arguments and create the prefix.
	arg_fmt = ', '.join(arg_fmts)
	prefix = '#### ' if small else '### '

	#	Get the function name, and escape it if it is protected.
	func_name = func.__name__
	if func_name.startswith('__'):
		func_name = f'\\_\\_{func_name[2:]}'

	#	Normalize triple+ newlines and return.
	return re.sub('\n\n+', '\n\n', f'{prefix}{func_name}({arg_fmt})\n{arg_descs}\n{doc_str}\n')

#	TODO: Provide plugin interface

def build_docs(package):
	'''
	Generate a Markdown file for each package in the __documented__ list in
	`package`.
	'''
	targets = [sys.modules[name] for name in package.__documented__]
	
	for package in targets:
		markdown = f'# {package.__name__}\n{package.__doc__}\n'

		#	Sort contents.
		classes, functions = [], []
		for attr in package.__all__:
			attr = getattr(package, attr)

			if inspect.isclass(attr):
				classes.append(attr)
			elif inspect.isfunction(attr):
				functions.append(attr)

		#	Document.
		if len(classes) > 0:
			markdown += f'\n## Classes\n'
			for cls in classes:
				c_doc = class_doc(cls)
				if c_doc is None:
					continue
				markdown += c_doc
		
		if len(functions) > 0:
			markdown += f'\n## Functions\n'
			for func in functions:
				f_doc = function_doc(func)
				if f_doc is None:
					continue
				markdown += f_doc

		#	Save.
		with open(f'{os.path.dirname(targets[0].__file__)}/../docs/code/{package.__name__}.md', 'w') as f:
			f.write(markdown)
