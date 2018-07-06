/*
*	Preset form field view definitions.
*/

@coreComponent
class FormViewExposure {
	constructor(core) {
		this.validatorTypes = {};

		this.defineDefaultValidators(core);
		this.defineFormViews(core);
	}

	@exposedMethod
	validator(type) {
		return ValidatorClass => {
			this.validatorTypes[type] = ValidatorClass;
		}
	}

	@exposedMethod
	readFile(file, callback) {
		let reader = new FileReader();
		reader.onload = event => {
			callback(event.target.result);
		}
		return reader.readAsDataURL(file);
	}
	
	defineDefaultValidators(core) {
		@this.validator('format')
		class RegexValidator {
			constructor(errorMessage=null, regex=null) {
				if (errorMessage) {
					this.errorMessage = errorMessage;
					this.info = {regex: regex, invert: false, ignore_case: false};
				}
			}

			validate(value) {
				let regex = (new RegExp('^' + this.info.regex + '$', this.info.ignore_case ? 'i' : ''));
				return !value || ((!!value.match(regex)) != this.info.invert);
			}
		}

		@this.validator('existance')
		class RequiredValidator {
			constructor(errorMessage='Required') {
				this.errorMessage = errorMessage;
			}

			validate(value, view, field) {
				return value !== '' && value !== null && value !== undefined;
			}
		}

		class FileTypeValidator {
			constructor(errorMessage, type) {
				this.errorMessage = errorMessage;
				this.type = type;
			}

			validate(value) {
				return value && value.type == this.type;
			}
		}

		@this.validator('range')
		class RangeValidator {
			constructor(errorMessage='Out of range', minValue=null, maxValue=null) {
				this.errorMessage = errorMessage;
				this.minValue = minValue;
				this.maxValue = maxValue;
			}

			setInfo(info) {
				this.minValue = info.min;
				this.maxValue = info.max;
			}

			validate(value) {
				let v = +value;
				return (
					(this.minValue === null || v >= this.minValue) &&
					(this.maxValue === null || v < this.maxValue)
				);
			}
		}

		core.RangeValidator = RangeValidator;
		core.RegexValidator = RegexValidator;
		core.RequiredValidator = RequiredValidator;
		core.FileTypeValidator = FileTypeValidator;
	}

	defineFormViews(core) {
		const self = this;

		@core.view({
			state: {error: null},
			template: state => 
				<div class={ "error-summary" + (state.error ? " active" : "") }>{ state.error }</div>
		})
		class ErrorSummary {
			attachToParent(parent) {
				parent.errorSummary = this;
			}

			show(error) { this.state.error = error; }
			hide() { this.state.error = null; }
		}
		
		@core.view({
			data: {},
			state: {
				error: null, 
				required: false, 
				gone: false, 
				classes: '',
				extra: '',
				value: null
			},
			template: (data, state) =>
				state.gone ? <span/> : <div class={ "field" + state.classes + (state.error ? " error" : "") + (state.required ? " required":  "") }>
					<label for={ data.name }>{ data.label }</label>
					<span class="input-container">
						{ data.type =='textarea' ?
							<textarea name={ data.name } class="input" placeholder={ data.placeholder }></textarea>
							:
							<input name={ data.name } class="input" type={ data.type } placeholder={ data.placeholder }/>
						}
					</span>
					<div class="error-message">{ state.error }</div>
					{ state.extra }
				</div>
		})
		class Field {
			onceConstructed(name, overrides={}) {
				this.name = name;
				this.overrides = overrides;
				this.unincluded = overrides.uninclude || false;
				this.transform = overrides.transform || (x => x);
				this.valueRenderer = overrides.valueRenderer || (x => x);
				this.model = overrides.model || null;
				this.changeCallback = overrides.changed || null;
				if (overrides.classes) {
					this.state.classes = ' ' + overrides.classes;
				}
				if (overrides.extra) {
					this.state.extra = overrides.extra;
				}

				this.validators = [];
			}
			
			get value() {
				return this.transform(this.state.value);
			}

			get files() {
				return this.element.querySelector('.input').files;
			}

			_doUpdate(value) {
				this.state.value = value;
				if (this.changeCallback) this.changeCallback(this, value);
				if (this.element.querySelector('.input') && this.data.type != 'file') {
					this.element.querySelector('.input').value = this.valueRenderer(value);
				}
			}

			setValueWithValidation(value) {
				this._doUpdate(value);
				this.validate();
			}

			set value(value) {
				this._doUpdate(value);
				return value;
			}

			get disabled() {
				let disabled = !!(this.overrides.when && !this.overrides.when(this));
				this.state.gone = disabled;
				return disabled;
			}

			render() {
				this.disabled;
				return super.render();
			}

			attachToParent(parent) {
				parent.addField(this);
			}

			invalidate(error) {
				this.state.error = error;
			}

			@core.event('.input', 'keyup')
			@core.event('.input', 'change')
			validateOrSubmit(context) {
				if (context.event.keyCode == 13 && this.data.type != 'textarea') {
					this.parent.submitForm();
				}
				else {
					let input = context.element;
					if (this.data.type == 'file') {
						this.setValueWithValidation(input.files[0]);
					}
					else {
						let value = input.value;
						if (this.data.type == 'number' && value != null) {
							value = +value;
						}
						this.setValueWithValidation(value);
					}
				}
			}

			validate() {
				this.state.error = null;
				if (this.parent.errorSummary) {
					this.parent.errorSummary.hide();
				}
				
				let value = this.value, input = this.element.querySelector('.input');
				for (let i = 0; i < this.validators.length; i++) {
					let validator = this.validators[i];
					if (!validator.validate(value, this, input)) {
						this.invalidate(validator.errorMessage);
						return;
					}
				}
				return !this.state.error;
			}

			onceCreated() {
				let model = this.model || this.parent.formModel || {},
					base = model[this.overrides.like || this.name] || {},
					resolve = key => (this.overrides[key] ? this.overrides[key] : base[key]);
				
				let label = this.overrides.label ? this.overrides.label 
						: this.name.replace(
							/(_|^)(\w)/g, (m, s, l) => (' ' + l.toUpperCase())
						).trim();
					
				//	Resolve validators.
				const addOne = validator => {
					validator.field = this;
					if (validator instanceof core.RequiredValidator) {
						this.state.required = true;
					}
					this.validators.push(validator);
				}
				let validatorDefns = resolve('validators') || [];
				for (var i = 0; i < validatorDefns.length; i++) {
					let validatorDefn = validatorDefns[i];
					if (validatorDefn.validate) {
						addOne(validatorDefn);
						continue;
					}
					let ValidatorClass = self.validatorTypes[validatorDefn.type];
					if (!ValidatorClass) throw 'No such validator type ' + validatorDefn.type;
					
					let validator = new ValidatorClass();
					if (validator.setInfo) {
						validator.setInfo(validatorDefn.info);
					}
					else {
						validator.info = validatorDefn.info;
					}
					validator.errorMessage = validatorDefn.error_message;
					addOne(validator);
				}

				this.data = {
					name: this.name,
					type: resolve('type') || 'text',
					label: label,
					placeholder: resolve('placeholder') || ''
				}
				setTimeout(this.render.bind(this), 1);
			}
		}

		core.Field = Field;
		core.ErrorSummary = ErrorSummary;
	}
}