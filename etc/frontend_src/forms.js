function Form(element){
	/*
		Form abstration object.
	*/
	var self = this;
	this.element = element;
	this.keys = [];
	this.content = {};
	this.defaultErrors = {};
	this.required = {};
	this.validators = {};
	this.errors = {};
	this.onSuccess = tk.fn.eatCall;
	this.submitting = false;

	this.success = function(callback){
		this.onSuccess = callback;
	}
	
	this.validate = function(){
		var key = tk.varg(arguments, 0, null);
		if (key != null){
			var value = tk.varg(arguments, 1, this.content[key]),
				validator = this.validators[key],
				pass = (value === null && !(this.required[key] && this.submitting)) || validator(value);
			this.errors[key] = pass ? null : this.defaultErrors[key];
			return pass;
		}
		else {
			var pass = true;
			tk.iter(self.keys, function(key){
				if (!self.validate(key)){
					pass = false;
				}
			});
			return pass;
		}
	}

	this.submit = function(){
		this.submitting = true;
		if (this.validate()){
			var fileInput = this.element.children('[type="file"]');
			if (fileInput.length > 0 && arguments.length == 0){
				//	TODO: Messy.
				if (fileInput.length != 1){
					throw 'Only one file upload per form supported';
				}

				var reader = new FileReader(), 
					toSend = tk.unbound(this.content),
					file = fileInput.ith(0, false).files[0];
				reader.onload = function(event){
					toSend[fileInput.attr('name')] = {
						data: btoa(event.target.result),
						mimetype: file.mimetype,
						name: file.name
					};
					self.submit(toSend);
				}
				reader.readAsBinaryString(file);
				core.flashMessage = 'Uploading files...';
				return;
			}

			var toSend = tk.varg(arguments, 0, tk.unbound(this.content));
			
			//	Add additional.
			var sendSpec = this.element.is('[cv-send-action]') ? this.element : this.element.children('[cv-send-action]');
			if (!sendSpec.empty){
				toSend.action = sendSpec.attr('cv-send-action');
			}
			
			var specURL = element.attr('cv-submit-to');
			core.request('POST', specURL == null ? core.route : specURL)
				.json(toSend)
				.success(self.onSuccess)
				.failure(function(response){
					if (response.status == 'error'){
						core.flashMessage = 'An error occurred';
						return;
					}

					var summary = tk.prop(response.data, 'error_summary', null);
					self.element.snap('p.error-summary:class(hidden null()):text', summary);

					tk.iter(tk.prop(response.data, 'errors', {}), function(key, value){
						self.errors[key] = value;
					});
				})
				.send();
		}
		this.submitting = false;
	}
	
	this.populate = function(source){
		tk.iter(self.keys, function(k){
			self.content[k] = tk.prop(source, k, null);
		});
	}

	//	Initialize.
	var contentBinding = tk.binding.on(this.content),
		errorBinding = tk.binding.on(this.errors);
	element
		.on('submit', function(e, event){
			self.submit();
			event.preventDefault();
		})
		.children('[name]').iter(function(e){
			var key = e.attr('name'),
				field = e.parents('.field').first(),
				error = e.attr('cv-error');

			//	Populate defaults.
			self.keys.push(key);
			self.content[key] = e.value();
			self.defaultErrors[key] = error === null ? 'Required' : decodeURIComponent(error);
			self.errors[key] = null;
			self.required[key] = e.is('[required]');
			
			if (e.is('[cv-validator]')){
				var repr = e.attr('cv-validator'),
					k = repr.indexOf(':'), 
					type = repr.substring(0, k);
				repr = repr.substring(k + 1);
				self.validators[key] = function(value){
					return core.storage.validators[type](repr, value);
				}
			}
			else {
				self.validators[key] = function(value){
					return !self.required[key] || value !== null;
				};
			}

			//	Begin implicit validation.
			contentBinding(key)
				.changed(function(newValue){
					if (newValue != e.value()){
						e.value(newValue);
					}
					self.validate(key, newValue);
				})
				.begin();

			//	Begin error binding.
			errorBinding(key)
				.changed(function(newValue){
					field.snap('$e:class(error notnull())>div.error-desc:html', newValue);
				})
				.begin();
			
			//	Attach update callback.
			e.on({
				keyup: function(e){
					self.content[key] = e.value();
				},
				change: function(e){
					self.content[key] = e.value();
				}
			});
		});
	tk.log('Created form (with action ' + element.attr('cv-send-action') + '): ', this);
}

tk.inspection(function(check){
	check.reduce('form').iter(function(e){
		var form = new Form(e);
		self.storage.forms[e.attr('cv-send-action')] = form;
		self.storage.form = self.storage.form || form;
	});
});

this.form = function(){
	/*
		Return the first form, or the form with a given `cv-send-action`.
	*/
	if (arguments.length == 0){
		return this.storage.form;
	}
	else {
		return this.storage.forms[arguments[0]];
	}
}

this.forms = function(){
	return this.storage.forms;
}
