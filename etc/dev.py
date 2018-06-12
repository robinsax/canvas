routes = {
	'/api/b/a/<q>': 11,
	'/api/b/<x>/<n>': 43
}

class Variable:

	def __init__(self, name):
		self.name = name

	def __hash__(self):
		return hash('%%var%%')
	
	def __eq__(self, other):
		return other == '%%var%%'

	def __str__(self):
		return '<Variable %s>'%self.name

	def __repr__(self):
		return str(self)

root = dict()
import re

for route in routes:
	cur = root
	parts = route[1:].split('/')
	for i, part in enumerate(parts):
		var_defn = re.match(r'^<(\w+)>$', part)
		if var_defn:
			part = Variable(var_defn.group(1))
		
		if part in cur:
			cur = cur[part]
		else:
			cur[part] = dict() if i != len(parts) - 1 else routes[route]
			cur = cur[part]
			

from json import dumps
print(root)

def resolve(route):
	cur = root
	variables = dict()
	for region in route[1:].split('/'):
		if not isinstance(cur, dict):
			raise NotImplementedError()
		if region in cur:
			cur = cur[region]
		elif '%%var%%' in cur:
			keys = list(cur.keys())
			variables[keys[keys.index('%%var%%')].name] = region
			cur = cur['%%var%%']
		else:
			raise NotImplementedError()
	if isinstance(cur, dict):
		raise NotImplementedError()
	return cur, variables

import sys
print(resolve(sys.argv[1]))
