class Field {
	constructor(options) {
		
	}

	render() {
		return 
	}
}

class Form {
	constructor(name) {
		
	}
}

@part
class FormPart {
	constructor(core) {
		this.validatorTypes = {}

		core.field = (options) => new Field(options);
		core.form = (options) => new Form(options);
		core.validator = (type) => this.registerValidatorType(type);

		core.onceReady(() => this.defineDefaultValidatorTypes());
	}

	registerValidatorType(type) {
		return target => { this.validatorTypes[type] = target; }
	}

	defineDefaultValidatorTypes() {
		@this.registerValidatorType('regex')
		class RegexValidator {
			constructor(repr) {
				let parts = repr.split(':');
				this.regex = new RegExp(decodeURIComponent(parts[0]), +parts[1] > 0 ? 'i' : '');
				this.negation = +parts[2] > 0;
			}

			validate(value) {
				return this.negation != this.regex.test(value);
			}
		}

		@this.registerValidatorType('range')
		class RangeValidator {
			constructor(repr) {
				let parts = repr.split(':');
				this.min = parts[0] == '-' ? null : +parts[0];
				this.max = parts[1] == '-' ? null : +parts[1];
			}

			validate(value) {
				return (!this.min || value >= this.min) && (!this.max || value <= this.max);
			}
		}

		@this.registerValidatorType('required')
		class RequiredValidator {
			validate(value) {
				return !!value;
			}
		}
	}
}
