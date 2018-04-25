class Field {
	//	TODO: Make use live template.

	constructor(options, form) {
		core.utils.applyOptionalizedArguments(this, options, {
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
				})
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
		return this.node.children('.input').value();
	}

	set value(value) {
		this.node.children('.input').value(value);
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

	bind(el) {
		let input = el.children('[name="' + this.name + '"]');
		if (input.empty) {
			return;
		}
		
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
	constructor() {
		this._formDefinitions = {};
		this.validatorTypes = {};
		core.forms = this.forms = {};

		core.readFile = (file, success) => this.readFile(file, success);

		core.form = (name, options) => this.form(name, options);
		
		core.onSuccess = core.utils.createMethodDecorator('_onSuccess');
		core.onFailure = core.utils.createMethodDecorator('_onFailure');

		core.onceReady(() => { 
			this.defineDefaultForms();
		});
		tk(window).on('load', () => this.createForms());
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
			tk.log('Created form ' + formName + ' as ' + label);
		});
	}

	form(options) {
		return (FormClass) => {
			class Form extends FormClass {
				constructor() {
					super();

					let definition = options.model ? modelDefinitions[options.model] : null;
					this.updateOptionDefaults = this.updateOptionDefaults || (x => x);
					
					core.utils.applyOptionalizedArguments(this, options, this.updateOptionDefaults({
						template: fields => 
							<div class="form">
								<div class="error-summary hidden"/>
								{ fields }
								<input type="submit">Submit</input>
							</div>,
						target: cv.route,
						method: 'post',
						uninclude: [],
						state: {}
					}));
					
					let fieldData = definition || {};
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
					
					this.base = {
						select: () => this.node,
						render: () => {
							if (this._rendering) { return; }
							this._rendering = true;
							
							let renderFields = (range) => {
								range = range || [0, tk.comp(this.fields, x => x).length];
								let curI = 0,
									result = [];

								tk.iter(this.fields, (name, field) => {
									if (curI >= range[0] && curI < range[1]) {
										result.push(field.template);
									}
									
									curI++;
								});
								
								return result;
							};

							this.node = this._templateContext
								.data(renderFields, this.state)
								.render();

							if (!this._created) {
								this._created = true;
								tk.listener(this, 'state').changed(() => { this.render(); })
							}

							core.utils.installObjectObservers(this.state, () => this.render());

							this._rendering = false;
							return this.node;
						},
						validate: () => {
							let pass = true;
							tk.iter(this.fields, (name, field) => {
								if (!field.validate()) {
									pass = false;
								}
							});

							return pass;
						},
						clear: () => {
							tk.iter(this.fields, (name, field) => {
								field.value = '';
							});
						},
						fill: content => {
							tk.iter(content, (key, value) => {
								let field = this.fields[key];
								if (field) {
									field.value = value;
								}
							});
						},
						submit: (includeData={}) => {
							if (!this.validate()){ return; }

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
							tk.iter(includeData, (k, v) => { data[k] = v; });

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

									core.utils.invokeDecoratedMethods(this, FormClass, '_onFailure', data.errors, data.error_summary);
								})
								.success(response => {
									core.utils.invokeDecoratedMethods(this, FormClass, '_onSuccess', response.data);
								})
								.send();
						}
					}
					
					tk.iter(this.base, (key, func) => {
						if (!this[key]) {
							this[key] = (...a) => func(...a);
						}
					});
					core.utils.invokeDecoratedMethods(this, FormClass, '_onSetup');

					Object.defineProperties(this, {
						_rendering: {
							value: false,
							writable: true,
							enumerable: false
						},
						_created: {
							value: false,
							writable: true,
							enumerable: false
						}
					});
					
					this.node = null;
					this._templateContext = tk.template(this._template || this.template)
						.live()
						.inspection(el => {
							tk.iter(this.fields, (name, field) => { field.bind(el); });

							core.utils.resolveEventsAndInspections(this, FormClass, el);

							el.reduce('input[type="submit"]').on('click', (el, event) => { 
								this.submit(); 
								event.preventDefault();
							});
							
							el.reduce('input').on('change', () => {
								el.children('.error-summary').classify('hidden');
							});
						});

				}
			}

			this._formDefinitions[FormClass.name.toLowerCase()] = Form;
			return Form;
		}
	}

	defineDefaultForms() {
		class ModalForm {
			constructor() {
				this.isOpen = false;

				this._template = (fields, data) => 
					<div class={ "modal" + (this.className ? " " + this.className : "") + (this.isOpen ? " open" : "") }>
						<div class="panel">
							<i class="fa fa-times close"/>
							{ this.template(fields, data) }
						</div>
					</div>
			}

			updateOptionDefaults(defaults) {
				defaults.className = null;
				return defaults;
			}

			@core.event('.modal, .close')
			@core.onSuccess
			close() {
				this.isOpen = false;
				this.select().classify('open', false);
			}
			
			open() {
				this.isOpen = true;
				this.select().classify('open');
			}
		
			@core.event('.panel')
			keepOpen(el, event) {
				event.stopPropagation();
			}
		}

		core.ModalForm = ModalForm;
	}
}
