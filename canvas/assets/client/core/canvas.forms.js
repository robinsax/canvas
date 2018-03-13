class Field {
	contructor(element) {
		this.element = element;
		this.name = element.attr('name');
		this.required = element.attr('required') != null;
		this.select = element.is('select');
		this.container = element.parents('.field').first();

		//	Read validator.
		this.validator = () => { return true; }
		let validatorDefn = element.attr('cv-validator');
		if (validatorDefn){
			let firstColon = validatorDefn.indexOf(':'),
				validatorType = validatorDefn.substring(0, firstColon);
			validatorDefn = validatorDefn.substring(firstColon);
			this.validator = (value) => {
				return cv.validators[validatorType](validatorDefn, value);
			}
		}

		this.defaultError = element.attr('cv-error');
		if (this.defaultError){
			this.defaultError = decodeURIComponent(this.defaultError);
		}
	}

	get value() {
		let value = this.element.value();
		if (this.select && value == '__null__'){
			value = null;
		}
		return value;
	}

	set value(value) {
		if (this.select && value == null){
			value = '__null__';
		}
		this.element.value(value);
	}

	validate(hard=false) {
		this.container.classify('error', false);

		if (!this.validator(this.value)){
			this.error();
			return false;
		}
		else if (hard && this.required && this.value == null){
			this.error('Required');
			return false;
		}
		return pass;
	}

	error(message=null){
		message = message || this.defaultError;
		this.container
			.classify('error')
			.children('.error-desc').text(message);
	}
}

class Form {
	constructor(element) {
		this.element = element;

		//	Replace submission event.
		this.element.on('submit', (el, event) => {
			this.submit();
			event.preventDefault();
		});

		//	Parse fields.
		this.keys = [];
		this.fields = {};

		this._success = null;
		this._process = (x) => { return x; };

		this.element.children('[name]')
			.iter((el) => {
				var field = new Field(el);
				this.keys.push(field.name);
				this.fields[field.name] = field;
			});
	}

	iter(callback) {
		tk.iter(this.keys, (name) => {
			callback(this.fields[name]);
		});
	}

	success(callback) {
		this._success = callback;
		return this;
	}

	process(callback) {
		this._process = callback;
		return this;
	}

	clear() {
		this.iter((field) => {
			field.value = null;
		});
	}

	populate(source) {
		tk.iter(source, (name, value) => {
			this.fields[name].value = value;
		});
	}

	validate() {
		let pass = false;
		this.iter((field) => {
			if (!field.validate(true)){
				pass = false;
			}
		});
		return pass;
	}

	submit() {
		if (!this.validate()){
			return;
		}

		let data = [];
		this.iter((field) => {
			data[field.name] = field.value;
		});

		//	TODO: Do we want this?
		let el = this.element.children('[cv-submit-action]');
		if (!el.empty){
			data.action = el.attr('cv-submit-action');
		}
		el = this.element.children('[cv-submit-url]');
		targetURL = el.empty ? cv.route : el.attr('cv-submit-url');

		doSubmit = () => {
			data = this._process(data);

			var request = cv.request('POST', targetURL)
				.json(data)
				.failure((response) => {
					if (response.status == 'error'){
						cv.flashMessage = 'An error occurred';
						return
					}
					
					this.element.children('.error-summary')
						.classify('hidden', response.data.error_summary !== undefined)
						.text(response.data.error_summary || '');
					
					if (response.data.errors){
						tk.iter(response.data.errors, (key, error) => {
							this.fields[key].error(error);
						});
					}
				});
			
			if (this._success){
				request.success(this._success);
			}

			request.send();
		}
		
		let fileInputs = this.element.children('[type="file"]');
		if (fileInputs.empty){
			doSubmit();
		}
		else {
			let complete = 0;
			//	TODO: Configurable.
			cv.flashMessage = 'Uploading files...';
			fileInputs.iter((input) => {
				let reader = new FileReader(),
					file = input.first(false)
						.files[0];

				reader.onload = (event) => {
					data[input.attr('name')] = {
						content: btoa(event.target.result),
						mimetype: file.mimetype,
						filename: file.name,
						_is_file: true
					}
					if (fileInputs.length == ++complete){
						doSubmit();
					}
				}
				reader.readAsBinaryString(file);
			});
		}
	}
}

@loader.attach
class FormPart {
	constructor(core) {
		this.forms = {}
		this.first = null

		core.Form = Form;
		core.form = (id=null) => {
			return id ? this.forms[id] : this.first;
		}
	}

	init() {
		//	Create forms.
		tk('form').iter((el) => {
			let form = new Form(el);
			this.forms[el.attr('id')] = form;
			this.first = this.first || form;
		});
	}
}
