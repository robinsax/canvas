# coding: utf-8
'''
The module manages a dictionary tree with controller leaves to allow 
approximately O(log n) route resolution. The tree is generated from a list of
controllers, as supplied by `create_controllers`, by `create_routing`. To 
modify the resultant route map at create time, register an `on_routing`
callback which takes the root of the route map dictionary as an argument.
The return value of the callback will be ignored.
'''

import re

from ..exceptions import NotFound
from ..utils import create_callback_registrar, logger

#	Create a log.
log = logger(__name__)

#	Define a variable sentinel that keyed RouteVariables can use to recognize each
#	other.
_variable_sentinel = object()
#	Define a sentinel key for on-branch leaf controllers.
_here_sentinel = object()
#	Define the root of the route map, a dictionary tree with controller leaves.
_route_map = dict()

#	Define the route map modification callback.
on_routing = create_callback_registrar()

def routing_diag():
	return (_route_map, _here_sentinel, _variable_sentinel)

class RouteVariable:
	'''Used to store named variable route parts.'''

	def __init__(self, name):
		'''::name The name of the variable for the eventual `RouteString`.'''
		self.name = name

	def __hash__(self):
		return hash(_variable_sentinel)
	
	def __eq__(self, other):
		return other is _variable_sentinel

	def __repr__(self):
		return '<RouteVariable "%s">'%self.name

class RouteString(str):
	'''
	The string used to contain the current route within the request context.
	If a route has variables, their values are accessible as attributes of
	this string.
	'''

	def populated(self, variables):
		self.__variables__ = list(variables.keys())
		for key, value in variables.items():
			setattr(self, key, value)
		return self

	def has_variable(self, variable):
		return variable in self.__variables__

def create_routing(controller_list):
	'''
	Populate the global route map with the `Controller`s in `controller_list`.
	'''
	
	#	Define a route map updater.
	def update_route_map(route, controller):
		#	Follow this route into the route map, generating branches and
		#	placing the controller as a leaf.
		current_node, last_node, last_key = _route_map, None, None
		route_parts = route[1:].split('/')
		for i, route_part in enumerate(route_parts):
			#	Check if this is a variable definition, updating the key
			#	to a variable if it is.
			variable_definition = re.match(r'^<(\w+)>$', route_part)
			if variable_definition:
				route_part = RouteVariable(variable_definition.group(1))
			
			#	Assert this isn't a leaf; if it is, make it on-branch.
			if not isinstance(current_node, dict):
				new_current_node = dict()
				new_current_node[_here_sentinel] = current_node
				last_node[last_key] = current_node = new_current_node

			if route_part not in current_node:
				#	Expand the tree.
				if i == len(route_parts) - 1:
					current_node[route_part] = controller
				else:
					current_node[route_part] = dict()
			
			last_node, last_key = current_node, route_part
			current_node = current_node[route_part]
	
	#	Update the route map for all routes for all controllers.
	for controller in controller_list:
		for route in controller.__routes__:
			update_route_map(route, controller)

	#	Invoke modification callbacks.
	on_routing.invoke(_route_map)
	
	log_routing(_route_map)

def resolve_route(route):
	current_node, variables = _route_map, dict()

	#	Follow this route into the map to a controller leaf, raising `NotFound`
	#	if any traversal error occurs and collecting encountered variables.
	for route_part in route[1:].split('/'):
		if not isinstance(current_node, dict):
			#	Went too far.
			raise NotFound(route)
		if route_part in current_node:
			#	Traverse deeper.
			current_node = current_node[route_part]
		elif _variable_sentinel in current_node:
			#	Retreive the encountered RouteVariable and store a value for it.
			#	Optimized for the non-variable case.
			key_list = list(current_node.keys())
			variable_name = key_list[key_list.index(_variable_sentinel)].name
			variables[variable_name] = route_part
			#	Traverse deeper.
			current_node = current_node[_variable_sentinel]
		else:
			#	No further branch.
			raise NotFound(route)
	if isinstance(current_node, dict):
		#	Check for an on-branch leaf.
		if _here_sentinel in current_node:
			return current_node[_here_sentinel], variables
		#	Didn't reach a controller.
		raise NotFound(route)
	return current_node, variables

def log_routing(routing):
	'''Log a formatted representation of the given route map.'''
	if not len(routing):
		log.info('Created null routing')
		return

	def name_key(key):
		if key is _here_sentinel:
			return '/.'
		elif isinstance(key, RouteVariable):
			return '/<%s>'%key.name
		else:
			return '/%s'%key
	
	def name_value(value):
		return '%s (%s)'%(
			value.__class__.__name__,
			', '.join(value.__verbs__)
		)

	def key_sort_child(child):
		if not isinstance(child[1], dict):
			return -1
		else:
			return len(child[1])

	def format_one(level):
		if not isinstance(level, dict):
			return name_value(level)
		else:
			key_lengths = list(len(name_key(key)) for key in level.keys())
			key_lengths.append(10)
			indent = ' '*(max(key_lengths) + 1)
			parts = list()
			for key, value in sorted(level.items(), key=key_sort_child):
				child_str = format_one(value).replace('\n', '\n' + indent)
				parts.append(name_key(key) + (indent[len(name_key(key)):]) + child_str)
			return '\n'.join(parts)

	log.info('Created routing:\n%s', format_one(routing))