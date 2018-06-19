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

	defineDefaultValidators(core) {
		@this.validator('format')
		class RegexValidator {
			validate(value) {
				let regex = (new RegExp('^' + this.info.regex + '$', this.info.ignore_case ? 'i' : ''));
				return !value || ((!!value.match(regex)) != this.info.invert);
			}
		}

		@this.validator('existance')
		class RequiredValidator {
			validate(value) {
				return value !== '' && value !== null;
			}
		}

		core.RegexValidator = RegexValidator;
		core.RequiredValidator = RequiredValidator;
	}

	defineFormViews(core) {
		const self = this;

		@core.view({
			state: {error: null},
			template: state => 
				<div class="error-summary">{ state.error }</div>
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
			state: {error: null},
			template: (data, state) => 
				<div class={ "field" + (state.error ? " error" : "") }>
					<label for={ data.name }>{ data.label }</label>
					<input name={ data.name } class="input" type={ data.type } placeholder={ data.placeholder }/>
					<div class="error-message">{ state.error }</div>
				</div>
		})
		class Field {
			constructor(name, overrides={}) {
				this.name = name;
				this.overrides = overrides;

				this.validators = [];
			}
			
			get value() {
				let value = this.element.querySelector('.input').value;
				if (this.data.type == 'number' && value != null) {
					value = +value;
				}
				return value;
			}

			attachToParent(parent) {
				parent.fields = parent.fields || {};
				parent.fields[this.name] = this;
			}

			invalidate(error) {
				this.state.error = error;
			}

			@core.event('.input', 'keyup')
			@core.event('.input', 'change')
			validate() {
				this.state.error = null;
				if (this.parent.errorSummary) {
					this.parent.errorSummary.hide();
				}
				
				for (let i = 0; i < this.validators.length; i++) {
					let validator = this.validators[i];
					if (!validator.validate(this.value)) {
						this.invalidate(validator.errorMessage);
						return;
					}
				}
				return !this.state.error;
			}

			onceCreated() {
				let base = this.parent.formModel ? this.parent.formModel[this.name] : {},
					resolve = key => (this.overrides[key] ? this.overrides[key] : base[key]);
				
				let label = this.overrides.label ? this.overrides.label 
						: this.name.replace(
							/(_|^)(\w)/g, (m, s, l) => (' ' + l.toUpperCase())
						).trim();
					
				//	Resolve validators.
				let validatorDefns = resolve('validators');
				for (var i = 0; i < validatorDefns.length; i++) {
					let validatorDefn = validatorDefns[i];
					let ValidatorClass = self.validatorTypes[validatorDefn.type];
					if (!ValidatorClass) throw 'No such validator type ' + validatorDefn.type;
					
					let validator = new ValidatorClass();
					validator.info = validatorDefn.info;
					validator.errorMessage = validatorDefn.error_message;
					this.validators.push(validator);
				}

				this.data = {
					name: this.name,
					type: resolve('type') || 'text',
					label: label,
					placeholder: resolve('placeholder') || ''
				}
			}
		}

		core.Field = Field;
		core.ErrorSummary = ErrorSummary;
	}
}