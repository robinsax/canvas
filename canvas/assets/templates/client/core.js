'use strict';
/*
	The canvas front-end core. Requires toolkit.js.

	TODO: Cleanup.
*/

//	Create the canvas toolkit instance.
var tk = createToolkit({
	debug: '{{ config.debug }}' == 'True',
	callbacks: {
		preRequest: function(req, xhr){
			//	Inform controllers they need to use action-based redirects.
			xhr.setRequestHeader('X-Canvas-View-Request', '1');
			if (req.fns.success === tk.fn.eatCall){
				//	Add an action check response.
				req.fns.success = function(response){
					if (tk.prop(response, 'data') && tk.prop(response.data, 'action')){
						core.storage.actions[response.data.action](response);
					}
				}
			}
		}
	}
});

function CanvasCore(){
	/*
		The canvas core object.
	*/
	var self = this;
	//	Insert configured style properties for reference.
	this.palettes = JSON.parse('{{ config.styling.palettes|json }}');
	this.breakpoints = JSON.parse('{{ config.styling.breakpoints|json }}');

	//	To contain current route and query string.
	this.route = null;
	this.query = {};
	//	To contain the meta page and page elements.
	this.metaPage = null;
	this.page = null;

	//	Alias a few toolkit properties.
	this.init = tk.init;
	this.debug = tk.config.debug;

	//	Storage.
	this.storage = {
		validators: {},
		actions: {},
		events: {},
		form: null,
		forms: {}
	};

	if (this.debug){
		function getAdditionLogger(added){
			return function(newValue){
				tk.log('Added ' + added + ':', newValue);
			}
		}

		tk.binding(this.storage, 'validators')
			.changed(getAdditionLogger('validator'))
			.begin();
		tk.binding(this.storage, 'actions')
			.changed(getAdditionLogger('action function'))
			.begin();
		tk.binding(this.storage, 'events')
			.changed(getAdditionLogger('event function'))
			.begin();
	}

	/* -- Plugin interface -- */
	//	List of loaded plugins.
	this.plugins = [];
	var unloadedPlugins = [];

	//	Define function decorators.
	function stored(map, fn, name){
		if (name === undefined){
			var declaration = fn.toString().match(/^function\s*([^\s(]+)/);
			if (declaration != null){
				name = declaration[1];
			}
			else {
				fn.__targetContainers__ = map;
			}
		}
		map[name] = fn;
		return fn;
	}
	//	Decorates controller-invokable actions.
	this.action = function(fn, name){ return stored(this.storage.actions, fn, name); }
	//	Decorates user-triggerable events.
	this.event = function(fn, name){ return stored(this.storage.events, fn, name); }
	//	Decorates live validator implementations.
	this.validator = function(fn, name){ return stored(this.storage.validators, fn, name); }

	//	The primary plugin interface.
	this.plugin = function(PluginClass){
		var cond = tk.varg(arguments, 1, true),
			condT = tk.typeCheck(cond, 'string', 'function', 'boolean');
		unloadedPlugins.push([
			PluginClass, cond, condT
		]);
	}

	//	Expose this in case plugins are loaded deferred.
	this.loadPlugins = function(){
		tk.iter(unloadedPlugins, function(packed){
			var plugin = packed[0], cond = packed[1],
				condT = packed[2];
			switch (condT){
				case 0:
					cond = self.route == cond;
					break;
				case 1:
					cond = cond();
					break;
				default:
					break;
			}
			if (cond){
				//	Create the instance.
				var inst;
				if (typeof plugin == 'function'){
					inst = new plugin();
				}
				else {
					inst = plugin;
				}
				tk.log('Loading plugin:', inst);
				//	Grab relevent methods.
				var prop = tk.prop.on(inst);
				if (prop('init')){
					initFns.push(function(){
						inst.init.apply(inst);
					});
				}
				if (prop('bind')){
					bindFns.push(inst.bind);
				}
				
				//	Catch deferred declarations.
				for (var pName in inst){
					var val = inst[pName];
					if (val == null){
						continue;
					}
					if (tk.prop(val, '__targetContainers__')){
						val.__targetContainers__[pName] = val;
					}
				}
			}
		});
		unloadedPlugins = [];
	}

	//	Base validator definitions.
	this.validator(function(repr, val){
		repr = repr.split(':');
		var obj = new RegExp(decodeURIComponent(repr[0]), repr[1] == '1' ? 'i' : ''),
			neg = repr[2] == '1';
		return neg != obj.test(val);
	}, 'regex');
	this.validator(function(repr, val){
		if (val == '' || val == null || val == undefined){
			return false;
		}
		repr = repr.split(',')
		var min = null, max = null;
		if (repr[0] != 'null'){
			min = parseFloat(repr[0]);
		}
		if (repr[1] != 'null'){
			max = parseFloat(repr[1]);
		}
		return (min == null || val >= min) && (max == null || val <= max);
	}, 'range');
	this.validator(function(repr, val){
		if (repr == 'any'){
			return val != '' && val != null && val != undefined;
		}
	}, 'option');
	this.validator(function(){
		return true;
	}, 'none');

	//	Base event definitions.
	this.event(function(src){
		//	Invoked by confirm being selected for a protected button.
		var group = src.parents('.condom').ith(0).children('.button');
		var original = group.reduce('.protected');
		self.storage.events[original.attr('cv-event')](original);
		group.classify('hidden', function(e){ return !e.is('.protected'); });
	}, '__confirm__');
	this.event(function(src){
		//	Invoked by cancel being selected for protected button.
		src.parents('.condom').ith(0)
			.children('.button')
			.classify('hidden', function(e){ return !e.is('.protected'); });
	}, '__cancel__');
	this.event(function(e, evt){
		evt.stopPropagation();
	}, '__block__');

	//	Core action definitions.
	this.action(function(response){
		window.location.href = response.data.url;
	}, 'redirect');
	this.action(function(response){
		//	Refresh page and prevent caching.
		var refresh = 1;
		var currentRefresh = self.query['refresh'];
		if (currentRefresh != null){
			refresh = (+currentRefresh) + 1;
		}
		window.location.href = window.location.pathname + '?refresh=' + refresh;
	}, 'refresh');

	//	Forms.
	this.validateField = function(field){
		var input;
		if (field.is(INPUT_SELECTOR)){
			input = field;
			field = field.parents('.field').ith(0);
		}
		else {
			input = field.children(INPUT_SELECTOR);
		}
		var repr = input.attr('cv-validator');
		var k = repr.indexOf(':'), type = repr.substring(0, k),
			repr = repr.substring(k + 1);
		var pass = validators[type](repr, input.value());
		field.classify('error', !pass)
			.children('.error-desc').text(input.attr('cv-error'));
		return pass;
	}
	this.fieldError = function(field){
		var input;
		if (field.is(INPUT_SELECTOR)){
			input = field;
			field = field.parents('.field').ith(0);
		}
		else {
			input = field.children(INPUT_SELECTOR);
		}
		field.classify('error', true)
			.children('.error-desc').text(tk.varg(arguments, 1, input.attr('cv-error')));
	}
	this.submitForm = this.event(function(src){
		src = src.extend(src.parents());
		//	Find form.
		var form = src.reduce('form', 1);
		if (form.empty){
			throw 'No form here';
		}

		//	Get action.
		var data = {};
		var actionSet = src.reduce('[cv-send-action]');
		if (!actionSet.empty){
			data.action = actionSet.attr('cv-send-action');
		}

		//	Validate fields.
		var errors = false;
		form.children(INPUT_SELECTOR).iter(function(e){
			if (self.validateField(e)){
				var val = e.value();
				data[e.attr('name')] = val === '' ? null : val;
			}
			else {
				errors = true;	
			}
		});
		if (errors){
			return;
		}

		//	Collect on-DOM parameters.
		src.reduce('[cv-param]').iter(function(e){
			//	Iterate each whitespace seperated pair.
			tk.iter(e.attr('cv-param').split(/\s+/g), function(p){
				var p = p.split('=');
				data[p[0]] = p[1];
			});
		});

		//	Check success callback.
		var win = tk.varg(arguments, 1, null);

		//	Send.
		var req = self.request()
			.json(data);
		if (win != null){
			req.success(win);
		}	
		req.failure(function(response){
				var summary = tk.prop(response.data, 'error_summary', null);
				if (summary != null){
					form.children('.error-summary')
						.text(summary)
						.classify('hidden', false);
				}
				tk.iter(tk.prop(response.data, 'errors', {}), function(k, v){
					var src = form.children('[name="' + k + '"]');
					if (src.empty){
						tk.log('Unmatched error: ' + k + ': ' + v);
					}
					else {
						self.fieldError(src, v);
					}
				});
			})
			.send();
	}, 'submit');

	//	Flash message function with binding.
	this.flashMessage = '';
	tk.init(function(){
		tk.binding(self, 'flashMessage')
			.onto(tk('.flash-message'))
				.placement(function(d, e){
					e.text(d).classify('hidden', false, 5000);
				})
			.and().begin();
	})
	this.event(function(e){
		self.flashMessage = e.attr('cv-message');
	}, 'flashMessage');
	this.action(function(response){
		self.flashMessage = response.data.message;
	}, 'flash_message');

	this.createTooltip = function(target, text){
		var pos = target.offset(),
			tooltip = tk.varg(arguments, 2, null);
		
		if (tooltip == null){
			tooltip = tk.tag('div', 'tooltip', text);
		}
		this.page.append(tooltip);

		var right = pos.x > self.page.size().width/2,
			scroll = this.page.ith(0, true).scrollTop;
		
		//	TODO: make right do something
		tooltip
			.css({
				'top': pos.y - scroll - 5 + 'px',
				'left': pos.x - 5 + 'px'
			})
			.classify('hidden', false)
			.classify('right', right);
		return tooltip;
	}

	//	toolkit AJAX with defaults.
	this.request = function(){
		var varg = tk.varg.on(arguments);
		return tk.request(varg(0, 'POST'), varg(1, window.location.href));
	}

	//	Form access
	this.form = function(){
		if (arguments.length == 0){
			return this.storage.form;
		}
		else {
			return this.storage.forms[arguments[0]];
		}
	}

	/* ---- Class definitions ---- */
	this.Modal = function(){
		var self = this;
		this.element = null;

		this.createPanel = function(){
			throw 'Not implemented.'
		}

		this.open = function(){
			this.element = tk('.page').append(
				tk.tag('div').classify('modal')
					.on('click', this.close)
					.append(
						tk.tag('div').classify('panel')
							.on('click', function(e, evt){ evt.stopPropagation() })
							.append(
								tk.tag('i')
									.classify('fa fa-times closer')
									.on('click', this.close)
							)
							.back().append(this.createPanel())
						.back()
					)
				.back()
			);
		}

		this.close = function(){
			self.element.remove();
		}
	}

	function inspectNodes(root){
		//	Bind callbacks.
		root.children('[cv-tooltip]').iter(function(e){
			var tooltip = null;
			e.on({
				'mouseover': function(){
					tooltip = self.createTooltip(e, e.attr('cv-tooltip'), tooltip);
				},
				'mouseleave': function(){
					tooltip.classify('hidden');
				}
			});
		});

		root.children('[cv-event]').iter(function(e){
			e.off('click').on('click', (function(){
				if (e.is('.button.protected')){
					return function(){
						e.parents('.condom').children('.button')
							.classify('hidden', function(g){ return e.equals(g); });
					}
				}
				else {
					return function(g, evt){
						var event = tk.prop(events, e.attr('cv-event'), null);
						if (event != null){
							event(e, evt);
						}
						else {
							throw 'No event ' + e.attr('cv-event');
						}
					}
				}
			})());
		});

		//	Setup on-page href nav.
		root.children('a[href]').iter(function(e){
			var href = e.attr('href');
			if (href[0] == '#'){
				var targ = tk(href);
				e.on('click', function(h, event){
					event.preventDefault();
					document.body.scrollTop = targ.offset().top;
					targ.classify('highlight', true, 1500);
				});
			}
		});

		root.children('form').iter(function(form){
			var data = {
				__errors__: {}
			};

			form.children('[name]').iter(function(input){
				var name = input.attr('name'),
					field = input.parents('.field').ith(0);
				
				data[name] = null;
				data.__errors__[name] = null;

				//	Create error message binding.
				tk.binding(data.__errors__, name)
					.changed(function(d){
						field.classify('error', d != null)
							.children('.error-desc')
							.text(d);
					})
					.begin();

				if (input.is('[cv-validator]')){
					//	Create validation binding.
					var repr = input.attr('cv-validator');
					
					//	Parse repr.
					var k = repr.indexOf(':'), 
						type = repr.substring(0, k);
					repr = repr.substring(k + 1);

					//	Bind listener to data value.
					tk.binding(data, name)
						.changed(function(d){
							input.value(d);
							var pass = self.storage.validators[type](repr, input.value());
							data.__errors__[name] = pass ? null : input.attr('cv-error');
						})
						.begin();
					
					function update(e){ data[name] = input.value(); }
					input.on({
						change: update,
						keyup: update
					});
				}
			});

			self.storage.forms[form.attr('id')] = data;
			if (self.storage.form === null){
				self.storage.form = data;
			}
		});
	}

	
	tk.init(function(){
		var body = tk('body');
		//	Parse DOM.
		self.route = body.attr('cv-route');
		self.page = body.children('.page', false);
		self.metaBody = body.children('.meta-body');

		//	Highlight open buttons.
		tk('.button').classify('open', function(e){
			return e.attr('href') == window.location.pathname;
		});

		//	Parse query string.
		tk.iter(window.location.search.substring(1).split('&'), function(p){
			p = p.split('=');
			self.query[decodeURIComponent(p[0])] = decodeURIComponent(p[1]);
		});

		//	Flash initial.
		var initial = self.metaBody.children('.init-message');
		if (!initial.empty){
			self.flashMessage = initial.text();
		}

		//	Load plugins.
		self.loadPlugins();

		//	Apply bindings.
		inspectNodes(body);
		tk.config.callbacks.preInsert = inspectNodes;		
	});
}
var core = new CanvasCore();
