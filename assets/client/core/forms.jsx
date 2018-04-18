class Field {
	constructor(options, form) {
		core.utils.applyOptionalizedArguments(this, options, {
			name: options.attribute,
			label: core.utils.nameToTitle(options.name),
			type: 'text',
			placeholder: '',
			validators: []
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
					repr = repr.substring(splitI);
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

		this.template = () => <div class={ "field" + (this._required ? " required" : "") }>
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
		if (toSet === _sentinel) {
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
						data: {}
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

							let el = tk.template(this._template || this.template)
								.data(() => tk.comp(this.fields, (k, f) => f.template), this.data)
								.render();

							core.utils.installObjectObservers(this.data, () => this.render());

							tk.iter(this.fields, (name, field) => { field.bind(el); });
							el.children('input[type="submit"]').on('click', (el, event) => { 
								this.submit(); 
								event.preventDefault();
							});
							el.children('input').on('change', () => {
								el.children('.error-summary').classify('hidden');
							});

							core.utils.resolveEvents(this, FormClass, el);

							if (this.node && !this.node.parents('body').empty){
								this.node.replace(el);
							}
							this.node = el;

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
								field.value('');
							});
						},
						fill: content => {
							tk.iter(content, (key, value) => {
								let field = this.fields[key];
								field && field.value(value);
							});
						},
						submit: (includeData={}) => {
							if (!this.validate()){ return; }

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
								.failure(response => {
									let data = response.data;
									if (data.errors) {
										tk.iter(data.errors, (name, error) => {
											this.fields[name].invalidate(error);
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
					
					tk.listener(this, 'data').changed(() => { this.render(); })

					Object.defineProperty(this, '_rendering', {
						value: false,
						writable: true,
						enumerable: false
					});
					this.node = null;
				}
			}

			this._formDefinitions[name] = Form;
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
