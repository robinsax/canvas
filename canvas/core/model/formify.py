#	coding utf-8
'''
Javascript form serialization.
'''

def serialize_form_data(model_cls):
	form_dict = dict()
	for name, column in model_cls.__schema__.items():
		constraints = []
		for constraint in column.constraints:
			try:
				constraints.append(constraint.as_client_parsable())
			except NotImplementedError: pass
		form_dict[name] = constraints
	print(form_dict)
