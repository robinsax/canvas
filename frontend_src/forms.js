function Form(element){
	/*
		Form abstration object.
	*/
	var self = this;
	this.element = element;
	this.keys = [];
	this.content = {};
	this.defaultErrors = {};
	this.validators = {};
	this.errors = {};
	
	this.validate = function(){
		var key = tk.varg(arguments, 0, null);
		if (key != null){
			var value = tk.varg(arguments, 1, this.content[key]),
				pass = this.validators[key](value);
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
		if (this.validate()){
			core.request()
				.json(this.content)
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
				field = e.parents('.field').first();

			//	Populate defaults.
			self.keys.push(key);
			self.content[key] = e.value();
			self.defaultErrors[key] = decodeURIComponent(e.attr('cv-error'));
			self.errors[key] = null;
			
			if (e.is('[cv-validator]')){
				var repr = e.attr('cv-validator'),
					k = repr.indexOf(':'), 
					type = repr.substring(0, k);
				repr = repr.substring(k + 1);
				self.validators[key] = function(value){
					return value == null || value.length == 0 || core.storage.validators[type](repr, value);
				}
			}
			else {
				self.validators[key] = tk.fn.tautology;
			}

			//	Begin implicit validation.
			contentBinding(key)
				.changed(function(newValue){
					e.value(newValue);
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
}

tk.inspection(function(root){
	root.children('form').iter(function(e){
		var form = new Form(e);
		self.storage.forms[e.attr('id')] = form;
		self.storage.form = self.storage.form || form;
	});
});

this.form = function(){
	/*
		Return the first form, or the form with a given `id`.
	*/
	if (arguments.length == 0){
		return this.storage.form;
	}
	else {
		return this.storage.forms[arguments[0]];
	}
}
