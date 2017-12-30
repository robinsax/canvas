var tk = createToolkit({
		debug: '{{ config.debug }}' == 'True',
		templateContainer: '.cv-templates',
		dataPrefix: 'cv',
		globalTemplateFunctions: {
			'cv_param_format': function(value, prop){
				return prop + '=' + value;
			},
			'cv_hide': function(value){
				return value ? 'hidden' : '';
			},
			'cv_show': function(value){
				return value ? '' : 'hidden';
			}
		}
	})
	.request.processor(function(r){
		r.setRequestHeader('X-Canvas-View-Request', '1');
	});

var cv = (function(){
	'use strict';
	var self = this;
	this.palettes = {{ config.styling.palettes }};
	this.breakpoints = {{ config.styling.breakpoints }};
	var INPUT_SELECTOR = 'input, textarea, select';

	this.query = {};
	var page;
	this.page = null;
	var clipboardStaging = null;

	//	Validator management
	var validators = {
		'regex': function(repr, val){
			repr = repr.split(':');
			var obj = new RegExp(decodeURIComponent(repr[0]), repr[1] == '1' ? 'i' : ''),
				neg = repr[2] == '1';
			return neg != obj.test(val);
		},
		'range': function(repr, val){
			repr = repr.split(',')
			var min = parseFloat(repr[0]), max = parseFloat(repr[1]);
			return val >= min && val <= max;
		},
		'none': function(){ return true; }
	}
	this.addValidators = function(add){
		for (var name in add){
			validators[name] = add;
		}
	}

	//	Action management
	var actions = {
		'__submit__': function(src){
			//	Submit the form at `src`
			self.submitForm(src);
		},
		'__confirm__': function(src){
			//	Invoked by confirm being selected for a 
			//	protected button
			var group = src.parents('.condom').ith(0).children('.button');
			var original = group.reduce('.protected');
			self.callAction(original.attr('cv-action'), original);
			group.classify('hidden', function(e){ return !e.is('.protected'); });
		},
		'__cancel__': function(src){
			//	Invoked by cancel being selected for a
			//	protected button
			var $condom = src.parents('.condom', false);
			var $src = src.parents('.condom').ith(0)
				.children('.button').classify('hidden', function(e){ return !e.is('.protected'); });
		},
		'multi': function(data){
			//	Call multiple actions
			var actions = data['actions'];
			for (var i = 0; i < actions.length; i++){
				self.callAction(actions[i], data);
			}
		},
		'show': function(arg, param){
			//	Show by selector
			tk(param('target')).classify('hidden', false);
		},
		'hide': function(arg, param){
			//	Hide by selector
			tk(param('target')).classify('hidden', true);
		},
		'toggle_hide': function(arg, param, isJSON){
			//	Toggle by selector
			tk(param('target')).classify('hidden', 'toggle');
		},
		'update_view': function(data){
			//	A generic content-update action for
			//	simple view updates
			var updates = data.updates;
			for (var id in updates){
				tk('#' + id).html(updates[id]);
			}
		},
		'flash_message': function(arg, param){
			//	Flash a message
			self.flash(param('message'));
		},
		'redirect': function(arg, param){
			//	Redirection for P-R-G, etc.
			window.location.href = param('url');
		},
		'refresh': function(arg){
			//	Refresh page and prevent caching
			var refresh = 1;
			var currentRefresh = self.query['refresh'];
			if (currentRefresh != null){
				refresh = parseInt(currentRefresh) + 1;
			}
			//	TODO: Handle edge cases
			window.location.href = window.location.pathname + '?refresh=' + refresh;
		},
		'clipboard': function(arg, param){
			//	TODO: Not working
			//	Copy element content to clipboard
			clipboardStaging.html(tk(param('target')).text())
				.select();
			try {
				if (document.execCommand('copy')){
					self.flash('Copied');
					return;
				}
			}
			catch (e){}
			self.flashError();
		}
	}
	this.addActions = function(o){
		tk.iter(o, function(name, fn){
			actions[name] = fn;
		});
	}
	this.callAction = function(action, arg){
		if (actions.hasOwnProperty(action)){
			var isJSON = !(arg instanceof tk.types.ToolkitInstance);
			
			function param(name){
				return isJSON ? arg[name] : arg.attr('cv-' + name);
			}
	
			actions[action](arg, param, isJSON);
		}
		else {
			throw 'No action ' + action;
		}
	}

	//	Combined mangement
	this.plugin = function(pl){
		if (tk.prop(pl, 'init')){
			this.addInitFunction(pl.init);
		}
		if (tk.prop(pl, 'actions')){
			this.addActions(pl.actions);
		}
		if (tk.prop(pl, 'validators')){
			this.addValidators(pl.validators);
		}
	}
	
	//	Sub-controller checking
	this.componentFor = function(loc){
		loc = loc.extend(loc.parents()).reduce('[cv-component]');
		if (!loc.empty){
			return loc.attr('cv-component');
		}
		return null;
	}

	//	Forms
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
	this.submitForm = function(src){
		src = src.extend(src.parents());
		//	Find form
		var form = src.reduce('form', 1);
		if (form.empty){
			throw 'No form here!';
		}

		//	Get action
		var data = {};
		var actionSet = src.reduce('[cv-send-action]');
		if (!actionSet.empty){
			data.action = actionSet.attr('cv-send-action');
		}

		//	Validate
		var errors = false;
		form.children(INPUT_SELECTOR).iter(function(e){
			if (self.validateField(e)){
				data[e.attr('name')] = e.value();
			}
			else {
				errors = true;	
			}
		});
		if (errors){
			return;
		}

		//	Collect more parameters
		src.reduce('[cv-param]').iter(function(e){
			//	Iterate each whitespace seperated pair
			tk.iter(e.attr('cv-param').split(/\s+/g), function(p){
				var p = p.split('=');
				data[p[0]] = p[1];
			});
		});

		//	Send
		cv.request(data, form, function(data){
			var summary = tk.prop(data, 'summary', null);
			if (summary != null){
				//	Show error summary
				form.children('.error-summary').text(summary)
					.classify('hidden', false, 5000);
			}
			tk.iter(tk.prop(data, 'errors', []), function(k, v){
				self.fieldError(form.children('[name="' + k + '"]'), v);
			});
		});
	}

	//	Flash messages
	var flashArea = null;
	this.flash = function(msg){
		flashArea.text(msg).classify('hidden', false, 5000);
	}
	this.flashError = function(){
		self.flash(tk.varg(arguments, 0, 'An error occurred'));
	}

	//	Canonical AJAX requests
	//	::argspec data, src, url, method, success, failure
	this.request = function(){
		var varg = tk.varg.on(arguments);
		var data = varg(0, {}, true),
			src = varg(1, null),
			success = varg(2, null),
			url = varg(3, window.location.href, true),
			method = varg(4, 'POST', true),
			failure = varg(5, self.flashError, true);
		
		if (src != null){
			data.__component__ = self.componentFor(src);
		}

		tk.debug('Sent (' + url + ', ' + method + '):', data);

		function handleResponse(response){
			tk.debug('Recieved:', response);
			
			var status = response.status, 
				data = tk.prop(response, 'data', {});
			if (status == 'error'){
				self.flashError();
			}
			else {
				if (success != null){
					success(data)
				}
				var action = tk.prop(data, 'action', null);
				if (action != null){
					self.callAction(action, data, status);
				}
			}
		}

		tk.request(url, method, data, handleResponse);
	}

	//	Mobile menu
	var mobileMenuModal = null, mobileMenu = null,
		mobileMenuButton = null, headerAreas = null,
		mobileMenuOpen = false, header = null;
	this.toggleMobileMenu = function(){
		var flag = tk.varg(arguments, 0, !mobileMenuOpen);
		if (mobileMenuOpen == flag){
			return;
		}
		mobileMenuOpen = flag;
		
		mobileMenuModal.classify('hidden', !flag);
		mobileMenuButton.classify('open', flag);
		
		(flag ? mobileMenu : header).append(headerAreas.remove());
	}

	function bind(root){
		//	Bind callbacks
		root.children('[cv-tooltip]').iter(function(e){
			var tooltip = null;
			e.on({
				'mouseover': function(){
					var pos = e.offset();
					if (tooltip == null){
						tooltip = tk.e('div', 'tooltip', decodeURIComponent(e.attr('cv-tooltip')));
						page.append(tooltip);
					}
					var right = pos.x > page.size().width/2;
					//	TODO: make right do something
					tooltip.css({
						'top': pos.y - 5 + 'px',
						'left': pos.x - 5 + 'px'
					})
					.classify('hidden', false)
					.classify('right', right);
				},
				'mouseleave': function(){
					tooltip.classify('hidden');
				}
			});
		});

		root.children('[cv-action]').iter(function(e){
			e.off('click').on('click', (function(){
				if (e.is('.button.protected')){
					return function(){
						e.parents('.condom').children('.button')
							.classify('hidden', function(g){ return e.equals(g); });
					}
				}
				else {
					return function(){
						self.callAction(e.attr('cv-action'), e);
					}
				}
			})());
		});

		root.children(INPUT_SELECTOR).iter(function(e){
			if (!e.is('[cv-validator]')){
				return;
			}
			var submits = !e.is('textarea');
			e.on({
				'keyup': function(h, event){
					if (submits && event.keyCode == 13){
						event.preventDefault();
						self.submitForm(e);
					}
					e.parents('form').children('.error-summary')
						.classify('hidden');
					self.validateField(e);
				},
				'keydown': function(h, event){
					if (submits && event.keyCode == 13){
						event.preventDefault();
					}
				}
			});
		});

		//	Setup on-page href nav
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
	}

	var initFns = [];
	this.addInitFunction = function(f){
		initFns.push(f);
	}
	function onInit(){
		//	Highlight open header button if present
		tk('.main-header .button').classify('open', function(e){
			return e.attr('href') == window.location.pathname;
		});

		//	Parse query string
		tk.iter(window.location.search.substring(1).split('&'), function(p){
			p = p.split('=');
			self.query[decodeURIComponent(p[0])] = decodeURIComponent(p[1]);
		});

		//	Grab elements
		page = tk('.full-page').on('click', function(e){
			tk('.button.menu-access.open').classify('open', false);
			tk('.menu').classify('hidden', true);
		});
		var meta = tk('.meta-page');
		clipboardStaging = meta.children('.clipboard-staging');
		header = page.children('header.main-header');
		headerAreas = header.children('.component.area', false);
		mobileMenuModal = page.children('.mobile-menu-modal')
			.on('click', function(){
				self.toggleMobileMenu(false);
			});
		mobileMenu = mobileMenuModal.children('.mobile-menu');
		mobileMenuButton = header.children('.button.mobile-menu-access')
			.on('click', function(){
				self.toggleMobileMenu();
			});
		flashArea = page.children('.flash-message')
		self.page = page;
		self.header = header;

		//	Create header highlighter
		//	TODO: packaging
		var highlighter = header.children('.button-highlight');
		header.children('.button').on({
			'mouseover': function(e){
				var w = e.size().width;
				highlighter.css({
					'opacity': 1,
					'width': w + 'px',
					'left': e.offset().x + w/2 + 'px'
				});
			},
			'mouseleave': function(e){
				highlighter.css('opacity', 0);
			}
		});

		//	Apply bindings
		bind(tk('body'));
		tk.config.bindFunction = bind;

		//	Flash initial
		var initial = meta.children('.init-message');
		if (!initial.empty){
			flash(initial.text());
		}

		tk.iter(initFns, function(f){
			f();
		});
	}
	tk.init(onInit);

	//	TODO: Packaging
	return this;
}).apply({});

{% block extras %}{% endblock %}
