//	TODO: serialize validators as objects.

class Validator {
	//	TODO: Avoid.

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
		let parts = repr.split('^');
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

@part
class ValidatorPart {
	constructor() {
		core._validatorTypes = this._validatorTypes = {};

		core._Validator = Validator;
		core.RegexValidator = RegexValidator;
		core.RangeValidator = RangeValidator;
		core.RequiredValidator = RequiredValidator;
		core.FileTypeValidator = FileTypeValidator;

		core.validator = (type) => this.registerValidatorType(type);
		core.onceReady(() => {
			this.defineDefaultValidatorTypes();
		});
	}
	
	registerValidatorType(type) {
		return target => { this._validatorTypes[type] = target; }
	}

	defineDefaultValidatorTypes() {
		@core.validator('regex')
		class _RegexValidator extends RegexValidator {}

		@core.validator('range')
		class _RangeValidator extends RangeValidator {}

		@core.validator('required')
		class _RequiredValidator extends RequiredValidator {}
	}
}
