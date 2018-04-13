#	coding utf-8
'''
Javascript form serialization.
'''

from .json_io import serialize_json

def serialize_form_models(model_classes):
	models_dict = dict()
	for model_cls in model_classes:
		form_dict = dict()
		for name, column in model_cls.__schema__.items():
			constraints = []
			for constraint in column.constraints:
				try:
					constraints.append((constraint.as_validator(), constraint.error_message))
				except NotImplementedError: pass
			form_dict[name] = {
				'type': column.input_type,
				'validators': constraints
			}
		models_dict[model_cls.__table__] = form_dict
	return serialize_json(models_dict)
