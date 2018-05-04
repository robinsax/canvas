class Field {
	//	TODO: Make use live template.

	constructor(options, form) {
		core.utils.putOptions(this, options, {
			name: options.attribute,
			label: core.utils.nameToTitle(options.name),
			type: 'text',
			placeholder: '',
			validators: [],
			options: []
		});
		Object.defineProperty(this, '_required', {
			value: false, 
			enumerable: false,
			writable: true
		});

		tk.iter(this.validators, (validator, i) => {
			if (!(validator instanceof core._Validator)) {
				let repr = validator[0],
				splitI = repr.indexOf(':'),
				type = repr.substring(0, splitI);

				if (splitI < 0){
					type = repr;
					repr = '';
				}
				else {
					repr = repr.substring(splitI + 1);
				}
					
				let Class = core._validatorTypes[type];
				if (!Class) {
					throw 'Unknown validator type ' + type;
				}
				let instance = new Class(repr);
				instance.errorMessage = validator[1];
				this.validators[i] = validator = instance;
			}
			
			if (validator instanceof RequiredValidator) {
				this._required = true;
			}
		});

		this.form = form;
		this.error = null;
		this.node = null;
		this.errorNode = null;
		this.changeCallbacks = [];

		if (this.type == 'select') {
			tk.listener(this, 'options').changed(() => {
				if (!this.node) {
					return;
				}

				this.node.children('option').remove();

				let select = this.node.children('select');
				if (this.placeholder) {
					select.append(tk.tag('option', null, this.placeholder));
				}
				tk.iter(this.options, item => {
					select.append(tk.tag('option', {value: item[1]}, item[0] + ''));
				});
			});
		}

		this.template = () => 
			<div class={ "field" + (this._required ? " required" : "") }>
				{ this.label ?
					<label for={ this.name }>{ this.label }</label>
					:
					() => {}
				}
				{ this.type == 'textarea' ? 
					<textarea class="input" name={ this.name }>{ this.placeholder }</textarea>
					: (
				  this.type == 'select' ?
					<select class="input" name={ this.name }>{ this.placeholder ? <option>{ this.placeholder }</option> : () => {} }</select>
					:
					<input class="input" name={ this.name } type={ this.type } placeholder={ this.placeholder }></input>
				)}
			</div>
	}

	get value() {
		let value = this.node.children('.input').value();
		return value == this.placeholder ? null : value;
	}

	set value(value) {
		this.node.children('.input').value(value);
	}

	onChange(callback) {
		this.changeCallbacks.push(callback);
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
			if (!validator.validate(this.value, this)){
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

	bindToNode(el, input) {
		input.on({
			keyup: (el, event) => {
				this.validate();
				if ((event.keyCode || event.which) == 13) {
					this.form.submit();
					event.preventDefault();
				}

				tk.iter(this.changeCallbacks, callback => {
					callback(this);
				});
			},
			change: () => {
				tk.iter(this.changeCallbacks, callback => {
					callback(this);
				});

				this.validate();
			}
		});

		this.node = el;
	}

	select() {
		return this.node;
	}
	
	render() {
		return this.bind(tk.template(this.template).render());
	}
}

class RootForm {
	__construct(options) {
		let model = options.model || this.model || null;
		this._modelDefn = model ? modelDefinitions[model] : {};

		let state = new core.State(this.state || {});
		state.update(options.state || {});
		Object.defineProperty(this, 'state', {
			value: state,
			writable: false
		});

		this.templates = this.templates || {};
		tk.update(this.templates, options.templates || {});

		this.template = options.template || this.template || this.templates.root || (fields => 
			<div class="form">
				<div class="error-summary hidden"/>
				{ fields }
				<input type="submit">Submit</input>
			</div>)
		
		this.target = options.target || this.target || core.route;
		this.method = options.method || this.method || 'post';
		this.uninclude = options.uninclude || this.uninclude || [];

		Object.defineProperties(this, {
			_rendering: {
				value: false,
				writable: true,
				enumerable: false
			},
			_templateContext: {
				value: null,
				writable: true,
				enumerable: false
			},
			_submitting: {
				value: false,
				writable: true,
				enumerable: false
			}
		});

		this.node = null;
		this.makeFields(options);
	}

	makeFields(options) {
		let fieldData = this._modelDefn || {};
		if (options.fields) {
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
			});
			
			fieldData = filteredFieldData;
		}

		this.fields = {};
		tk.iter(fieldData, (name, data) => {
			data.name = name;
			this.fields[name] = new Field(data, this);
		});
	}

	render() {
		if (this._rendering) { return; }
		this._rendering = true;
		
		let boundRender = this.render.bind(this);

		core.utils.installObjectObservers(this.state, boundRender);
		this.state._.toInstall = boundRender;

		if (!this._templateContext) {
			this._templateContext = tk.template(this.template)
				.live()
				.inspection(el => {
					core.utils.resolveEventsAndInspections(this, el);

					if (el.is('input[type="submit"]')) {
						el.on('click', (el, event) => { 
							this.submit(); 
							event.preventDefault();
						});
					}

					if (el.is('.field')) {
						let input = el.children('.input');
						this.fields[input.attr('name')].bindToNode(el, input);
					}
					
					el.reduce('input').on('change', () => {
						el.children('.error-summary').classify('hidden');
					});
				});
		}

		let renderFields = (range) => {
			range = range || [0, tk.comp(this.fields, x => x).length];
			let curI = 0, result = [];

			tk.iter(this.fields, (name, field) => {
				if (curI >= range[0] && curI < range[1]) {
					result.push(field.template);
				}
				
				curI++;
			});
			
			return () => <div class="fields">{ result }</div>;
		};

		this.node = this._templateContext
			.data(renderFields, this.state, this.templates)
			.render();
		
		this._rendering = false;
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

	fill(content) {
		tk.iter(content, (key, value) => {
			let field = this.fields[key];
			if (field) {
				field.value = value;
			}
		});
	}

	clear() {
		tk.iter(this.fields, (name, field) => {
			field.value = '';
		});
	}

	submit(extraData={}) {
		if (!this.validate() || this._submitting){ return; }
		this._submitting = true;

		let data = {};
		tk.iter(this.fields, (name, field) => {
			if (this.uninclude.indexOf(name) >= 0){
				return;
			}
			
			let value = field.value;
			if (value != null) {
				data[name] = value;
			}
		});
		tk.iter(extraData, (k, v) => { data[k] = v; });

		cv.request(this.method, this.target).json(data)
			.failure(response => {
				let data = response.data;
				if (data.errors) {
					tk.iter(data.errors, (name, error) => {
						let field = this.fields[name];
						if (field) {
							field.invalidate(error);
						}
						else {
							tk.warn('Invalidated field "' + name + '" not contained in form');
						}
					});
				}
				if (data.error_summary) {
					let summaryNode = this.select().children('.error-summary');
					if (summaryNode.empty) {
						tk.warn('Cannot display error summary; no .summary-area (was ' + data.error_summary + ')');
					}
					else {
						summaryNode.classify('hidden', false).text(data.error_summary);
					}
				}

				core.utils.invokeAnnotated(this, 'isFailureCallback', data.errors, data.error_summary);
				this._submitting = false;
			})
			.success(response => {
				core.utils.invokeAnnotated(this, 'isSuccessCallback', response.data);
				this._submitting = false;
			})
			.send();
	}

	select() { return this.node; }
}

@part
class FormPart {
	constructor() {
		this._formDefinitions = {};
		this.validatorTypes = {};
		
		core.Form = RootForm;

		core.readFile = (file, success) => this.readFile(file, success);

		core.form = (name, options) => this.form(name, options);
		core.forms = this.forms = {};
		
		core.onSuccess = core.utils.createAnnotationDecorator('isSuccessCallback');
		core.onFailure = core.utils.createAnnotationDecorator('isFailureCallback');
		
		tk(window).on('load', this.createForms.bind(this));
	}

	readFile(file, success) {
		let reader = new FileReader();
		reader.onload = event => {
			success(event.target.result);
		}
		return reader.readAsBinaryString(file);
	} 

	createForms() {
		core.utils.iterateNonStandardTags((el, formName) => {
			if (!this._formDefinitions[formName]){
				return;
			}

			let label = el.attr('data-name') || el.attr('name') || formName, 
				form = new this._formDefinitions[formName]();
			this.forms[label] = form;
			
			el.replace(form.render());
			tk.log('Created form ' + label);
		});
	}

	form(options) {
		return FormClass => {

			core.utils.setRootPrototype(FormClass, RootForm);
			let Form = (() => class Form extends FormClass {
				constructor() {
					super();
					this.__construct(options);
					core.attachMixins(this, options.mixins || []);
				}
			})();

			this._formDefinitions[FormClass.name.toLowerCase()] = Form;
			return Form;
		}
	}
}
