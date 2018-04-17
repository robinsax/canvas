let formPartInstance = null;
let _sentinel = {};

class Validator {
	constructor(errorMessage) {
		this.errorMessage = errorMessage;
	}

	validate(value) {
		throw 'Not implemented';
	}
}

class FileTypeValidator extends Validator {
	constructor(repr, errorMessage) {
		super(errorMessage);
		this.type = repr;
	}

	validate(value) {
		let pass = true;
		tk.iter([].slice.call(value), file => {
			if (file.type != this.type) {
				pass = false;
				return false;
			}
		});
		return pass;
	}
}

class RegexValidator extends Validator {
	constructor(repr, errorMessage) {
		super(errorMessage);
		let parts = repr.split(':');
		this.regex = new RegExp(decodeURIComponent(parts[0]), +parts[1] > 0 ? 'i' : '');
		this.negation = +parts[2] > 0;
	}

	validate(value) {
		return this.negation != this.regex.test(value);
	}
}

class RangeValidator extends Validator {
	constructor(repr, errorMessage) {
		super(errorMessage);
		let parts = repr.split(':');
		this.min = parts[0] == '-' ? null : +parts[0];
		this.max = parts[1] == '-' ? null : +parts[1];
	}

	validate(value) {
		return (this.min == null || value >= this.min) && (this.max == null || value <= this.max);
	}
}

class RequiredValidator extends Validator {
	constructor(repr) {
		super('Required');
	}

	validate(value, field) {
		if (field.type == 'file') {
			return value.length > 0;
		}
		return value != null;
	}
}

class Field {
	constructor(options, form) {
		let nameToTitle = (n) => {
			return n.replace(/(_|^)(\w)/g, (m, s, l) => (' ' + l.toUpperCase()));
		}
		this.name = options.name || options.attribute;
		this.label = options.label || nameToTitle(options.name);
		this.type = options.type || 'text';
		this.placeholder = options.placeholder || '';
		this.validators = options.validators || [];
		this.required = false;

		tk.iter(this.validators, (validator, i) => {
			if (!(validator instanceof Validator)) {
				let repr = validator[0],
				splitI = repr.indexOf(':'),
				type = repr.substring(0, splitI);

				if (splitI < 0){
					type = repr;
					repr = '';
				}
				else {
					repr = repr.substring(splitI);
				}
					
				let Class = formPartInstance.validatorTypes[type];
				if (!Class) {
					throw 'Unknown validator type ' + type;
				}
				let instance = new Class(repr);
				instance.errorMessage = validator[1];
				this.validators[i] = validator = instance;
			}
			
			if (validator instanceof RequiredValidator) {
				this.required = true;
			}
		});

		this.form = form;
		this.error = null;
		this.node = null;
		this.errorNode = null;

		this.template = () => <div class={ "field" + (this.required ? " required" : "") }>
				{ this.label ?
					<label for={ this.name }>{ this.label }</label>
					:
					() => {}
				}
				{ this.type == 'textarea' ? 
					<textarea class="input" name={ this.name }>{ this.placeholder }</textarea>
					:
					<input class="input" name={ this.name } type={ this.type } placeholder={ this.placeholder }></input>
				}
			</div>

	}

	value(toSet=_sentinel) {
		if (toSet == _sentinel) {
			return this.node.children('.input').value();
		}
		this.node.children('.input').value(toSet);
	}

	//	TODO: Cleanup.
	invalidate(error) {
		this.error = error;
		if (this.errorNode){
			this.errorNode.remove();
		}

		this.node.classify('error');

		this.errorNode = tk.tag('div', {class: 'error-message'}, this.error);
		this.node.append(this.errorNode);
	}

	validate() {
		this.error = null;
		if (this.errorNode){
			this.errorNode.remove();
		}

		tk.iter(this.validators, validator => {
			if (!validator.validate(this.value(), this)){
				this.error = validator.errorMessage;
			}
		});
		if (this.error) {
			this.node.classify('error');

			this.errorNode = tk.tag('div', {class: 'error-message'}, this.error);
			this.node.append(this.errorNode);
		}
		else {
			this.node.classify('error', false);
		}
		
		return !this.error;
	}

	bind(el) {
		let input = el.children('[name="' + this.name + '"]');
		input.on({
			keyup: (el, event) => {
				this.validate();
				if ((event.keyCode || event.which) == 13) {
					this.form.submit();
				}
			},
			change: () => {
				this.validate();
			}
		});

		this.node = input.parents(false);

		return el;
	}
	
	render() {
		return this.bind(tk.template(this.template).render());
	}
}

@part
class FormPart {
	constructor(core) {
		formPartInstance = this;
		this._formDefinitions = {};
		this.validatorTypes = {};
		core.forms = this.forms = {};

		core.RegexValidator = RegexValidator;
		core.RangeValidator = RangeValidator;
		core.RequiredValidator = RequiredValidator;
		core.FileTypeValidator = FileTypeValidator;

		core.readFile = (file, success) => this.readFile(file, success);

		core.form = (name, options) => this.form(name, options);
		core.validator = (type) => this.registerValidatorType(type);

		core.onSuccess = (target, key) => this.formOnSuccess(target, key);
		core.onFailure = (target, key) => this.formOnFailure(target, key);

		core.onceReady(() => { this.defineDefaultValidatorTypes() });
		tk(window).on('load', () => this.createForms());
	}

	readFile(file, success) {
		let reader = new FileReader();
		reader.onload = event => {
			success(event.target.result);
		}
		return reader.readAsBinaryString(file);
	} 

	registerValidatorType(type) {
		return target => { this.validatorTypes[type] = target; }
	}

	defineDefaultValidatorTypes() {
		@this.registerValidatorType('regex')
		class _RegexValidator extends RegexValidator {}

		@this.registerValidatorType('range')
		class _RangeValidator extends RangeValidator {}

		@this.registerValidatorType('required')
		class _RequiredValidator extends RequiredValidator {}
	}

	createForms() {
		tk('cv-form').iter(el => {
			let name = el.attr('cv-name'),
				Class = this._formDefinitions[name];
			if (!Class) {
				tk.warn('No such form ' + name);
				el.remove();
				return;
			}
			let instance = new Class();
			el.replace(instance.render());

			this.forms[el.attr('cv-label') || name] = instance;
		});
	}

	form(name, options) {
		return (FormClass) => {
			class Form extends FormClass {
				constructor() {
					super();
					let definition = null;
					if (options.model) {
						definition = modelDefinitions[options.model];
					}
					this.modelName = options.model || null;
					this.template = this.template || options.template || (fields => 
						<div class="form">
							{ fields }
							<input type="submit">Submit</input>
						</div>);
					this.target = this.target || options.target || cv.route;
					this.method = this.method || options.method || 'POST';
					this.uninclude = this.uninclude || options.uninclude || [];
					
					let fieldData = definition || {};
					if (options.fields) {
						//	TODO: Nasty.
						if (!definition) {
							tk.iter(options.fields, select => {
								let override = {};
								if (select instanceof Array){
									override = select[1];
									select = select[0];
								}
								fieldData[select] = {};
								tk.iter(override, (key, value) => {
									fieldData[select][key] = value;
								});
							})
						}
						else {
							let filteredFieldData = {};
							tk.iter(options.fields, select => {
								let override = {};
								if (select instanceof Array){
									override = select[1];
									select = select[0];
								}
								filteredFieldData[select] = fieldData[select] || {};
								tk.iter(override, (key, value) => {
									filteredFieldData[select][key] = value;
								});
							})

							fieldData = filteredFieldData;
						}
					}

					this.fields = {};
					tk.iter(fieldData, (name, data) => {
						data.name = name;
						this.fields[name] = new Field(data, this);
					});

					this.node = null;
				}

				select() {
					return this.node;
				}

				render() {
					this.node = tk.template(this.template)
						.data(() => tk.comp(this.fields, (k, f) => f.template))
						.render();
					
					tk.iter(this.fields, (name, field) => {
						field.bind(this.node);
					});

					this.node.children('input[type="submit"]').on('click', () => {
						this.submit();
					});

					//	TODO Patternize.
					if (FormClass.prototype._events) {
						tk.iter(FormClass.prototype._events, (eventDesc) => {
							if (this.node.is(eventDesc.selector)) {
								this.node.on(eventDesc.on, (tel, event) => {
									this[eventDesc.key](tel, event);
								});	
							}
							this.node.children(eventDesc.selector).on(eventDesc.on, (tel, event) => {
								this[eventDesc.key](tel, event);
							});
						});
					}

					return this.node;
				}

				validate() {
					let pass = true;
					tk.iter(this.fields, (name, field) => {
						if (!field.validate()) {
							pass = false;
						}
					});

					return pass;
				}

				clear() {
					tk.iter(this.fields, (name, field) => {
						field.value('');
					});
				}

				fill(content) {
					tk.iter(content, (key, value) => {
						let field = this.fields[key];
						field && field.value(value);
					});
				}

				submit(includeData={}) {
					if (!this.validate()){
						return;
					}

					let data = {};
					tk.iter(this.fields, (name, field) => {
						if (this.uninclude.indexOf(name) >= 0){
							return;
						}
						
						let value = field.value();
						if (value != null) {
							data[name] = value;
						}
					});
					tk.iter(includeData, (k, v) => { data[k] = v; });

					cv.request(this.method, this.target).json(data)
						.failure((response) => {
							let data = response.data;
							if (data.errors) {
								tk.iter(data.errors, (name, error) => {
									this.fields[name].invalidate(error);
								});
							}
							if (data.error_summary) {
								//	TODO: Nonono
								console.log('Summary was ' + data.error_summary);
							}
							if (FormClass.prototype._onFailure) {
								this[FormClass.prototype._onFailure](data.errors, data.error_summary);
							}
						})
						.success((response) => {
							if (FormClass.prototype._onSuccess) {
								this[FormClass.prototype._onSuccess](response.data);
							}
						})
						.send();
				}
			}

			this._formDefinitions[name] = Form;
			return Form;
		}
	}

	formOnSuccess(target, key) {
		target._onSuccess = key;
	}

	formOnFailure(target, key) {
		target._onFailure = key;
	}
}
