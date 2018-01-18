//	Create the canvas toolkit object
var tk = createToolkit({
		debug: '{{ config.debug }}' == 'True',
		templateContainer: '.cv-templates',
		dataPrefix: 'cv',
		globalTemplateFunctions: {
			//	Common template functions
			'hiddenIf': function(v){ return v ? 'hidden' : ''; },
			'hiddenIfNot': function(v){ return v ? '' : 'hidden'; },
			'hiddenIfNull': function(v){ return v == null ? 'hidden' : ''; },
			'hiddenIfNotNull': function(v){ return v == null ? '' : 'hidden'; }
		}
	})
	.request.processor(function(r){
		r.setRequestHeader('X-Canvas-View-Request', '1');
	});
//	Resolve the -event name conflict
tk.attrNames.event = 'cv-mapped-event';

//	Create canvas core object
//	TODO: Packaging (scope this tighter)
function CanvasCore(){
	'use strict';
	var INPUT_SELECTOR = 'input, textarea, select';

	//	Scoping helper
	var self = this;

	//	Insert configured style properties
	//	for reference
	this.palettes = JSON.parse('{{ config.styling.palettes|json }}');
	this.breakpoints = JSON.parse('{{ config.styling.breakpoints|json }}');

	//	To contain the query string
	this.query = {};
	//	To contain current route (although redundant 
	//	to canonical implementations)
	this.route = null;

	//	To contain the meta page element
	this.metaPage = null;
	//	To contain the root page element
	this.page = null;
	//	To contain the root header element
	this.header = null;

	//	Containers
	var initFns = [],
		bindFns = [],
		validators = {},
		actions = {},
		events = {};

	/* -- Plugin interface -- */
	//	List of loaded plugins
	this.plugins = [];
	//	Internal list of plugins to load when
	//	loadPlugins() called
	var unloadedPlugins = [];

	//	Function decorators
	function stored(map, fn, name){
		if (name === undefined){
			var declaration = fn.toString().match(/^function\s*([^\s(]+)/);
			if (declaration != null){
				name = declaration[1];
			}
			else {
				fn.__canvasAddTo = map;
			}
		}
		map[name] = fn;
		return fn;
	}
	this.action = function(fn, name){
		return stored(actions, fn, name);
	}
	this.event = function(fn, name){
		return stored(events, fn, name);
	}
	this.validator = function(fn, name){
		return stored(validators, fn, name);
	}
	this.mappedEvent = function(fn, name){
		return stored(tk.config.globalTemplateFunctions, fn, name);
	}
	
	//	Primary plugin interface
	this.plugin = function(PluginClass){
		var cond = tk.varg(arguments, 1, true),
			condT = tk.typeCheck(cond, ['string', 'function', 'boolean']);
		unloadedPlugins.push([
			PluginClass, cond, condT
		]);
	}

	//	Expose this in case plugins are loaded
	//	deferred
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
				//	Create the instance
				var inst;
				if (typeof plugin == 'function'){
					inst = new plugin();
				}
				else {
					inst = plugin;
				}
				tk.debug('Loading plugin:', inst);
				//	Grab relevent methods
				var prop = tk.prop.on(inst);
				if (prop('init')){
					initFns.push(inst.init);
				}
				if (prop('bind')){
					bindFns.push(inst.bind);
				}
				
				//	Catch deferred declarations
				for (var pName in inst){
					var val = inst[pName];
					if (tk.prop(val, '__canvasAddTo')){
						val.__canvasAddTo[pName] = val;
					}
				}
			}
		});
		unloadedPlugins = [];
	}

	//	Base validator definitions
	this.validator(function(repr, val){
		repr = repr.split(':');
		var obj = new RegExp(decodeURIComponent(repr[0]), repr[1] == '1' ? 'i' : ''),
			neg = repr[2] == '1';
		return neg != obj.test(val);
	}, 'regex');
	this.validator(function(repr, val){
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
	this.validator(function(){
		return true;
	}, 'none');

	//	Base event definitions
	this.event(function(src){
		//	Invoked by confirm being selected for a 
		//	protected button
		var group = src.parents('.condom').ith(0).children('.button');
		var original = group.reduce('.protected');
		events[original.attr('cv-event')](original);
		group.classify('hidden', function(e){ return !e.is('.protected'); });
	}, '__confirm__');
	this.event(function(src){
		//	Invoked by cancel being selected for a
		//	protected button
		src.parents('.condom').ith(0)
			.children('.button')
			.classify('hidden', function(e){ return !e.is('.protected'); });
	}, '__cancel__');
	this.event(function(e, evt){
		evt.stopPropagation();
	}, 'stopPropagation');

	this.openModal = function(template, data, functions){
		//	TODO: Hold page-content-wrap
		tk.map(data, template, tk('.page-content-wrap'), functions);
	}

	this.closeModal = this.event(function(e){
		e.extend(e.parents('.modal')).reduce('.modal').remove();
	}, 'closeModal');

	//	Core action definitions
	this.action(function(data){
		window.location.href = data.url;
	}, 'redirect');
	this.action(function(data){
		//	Refresh page and prevent caching
		var refresh = 1;
		var currentRefresh = self.query['refresh'];
		if (currentRefresh != null){
			refresh = (+currentRefresh) + 1;
		}
		//	TODO: Handle edge cases
		window.location.href = window.location.pathname + '?refresh=' + refresh;
	}, 'refresh');
	
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
	this.submitForm = this.event(function(src){
		src = src.extend(src.parents());
		//	Find form
		var form = src.reduce('form', 1);
		if (form.empty){
			throw 'No form here';
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
		self.request(data, form, function(data){
			var summary = tk.prop(data, 'error_summary', null);
			if (summary != null){
				//	Show error summary
				form.children('.error-summary').text(summary)
					.classify('hidden', false, 5000);
			}
			tk.iter(tk.prop(data, 'errors', []), function(k, v){
				self.fieldError(form.children('[name="' + k + '"]'), v);
			});
		});
	}, 'submit');

	//	Flash messages
	var flashArea = null;
	this.flash = function(msg){
		flashArea.text(msg).classify('hidden', false, 5000);
	}
	//	Event binding
	this.event(function(e){
		self.flash(e.attr('cv-message'));
	}, 'flashMessage');
	//	Action binding
	this.action(function(data){
		self.flash(data.message);
	}, 'flash_message');

	function flashError(){
		self.flash(tk.varg(arguments, 0, 'An error occurred'));
	}
	this.flashError = this.event(flashError);

	function createTooltip(target, text){
		var pos = target.offset();
		var tooltip = tk.varg(arguments, 2, null);
		if (tooltip == null){
			tooltip = tk.e('div', 'tooltip', text);
		}
		this.page.append(tooltip);
		var right = pos.x > self.page.size().width/2;
		//	TODO: make right do something
		tooltip.css({
			'top': pos.y - 5 + 'px',
			'left': pos.x - 5 + 'px'
		})
		.classify('hidden', false)
		.classify('right', right);
		return tooltip;
	}
	this.createTooltip = this.event(createTooltip);

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
				if (tk.prop(data, 'action')){
					actions[data.action](data);
				}
			}
		}

		tk.request(url, method, data, handleResponse);
	}

	function bind(root){
		//	Bind callbacks
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
				'change': function(h, event){
					//	TODO: Race cond.
					tk.defer(function(){
						e.parents('form').children('.error-summary')
							.classify('hidden');
						self.validateField(e);
					}, 100)
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

		tk.iter(bindFns, function(f){ f(); })
	}

	function init(){
		self.route = tk('body').attr('cv-route');

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
		self.page = tk('body > .page');
		self.meta = tk('.meta-page');
		self.header = self.page.children('header.main-header');
		flashArea = self.page.children('.flash-message')

		self.headerHighlight = function(e){
			var w = e.size().width;
			highlighter.css({
				'opacity': 1,
				'width': w + 'px',
				'left': e.offset().x + w/2 + 'px'
			});
		}

		//	Create header highlighter
		//	TODO: packaging
		//	TODO: Bring .common to core
		var highlighter = self.header.children('.button-highlight');
		self.header.children('.button:not(.common)').on({
			'mouseover': self.headerHighlight,
			'mouseleave': function(e){
				highlighter.css('opacity', 0);
			}
		});

		//	Flash initial
		var initial = self.meta.children('.init-message');
		if (!initial.empty){
			self.flash(initial.text());
		}

		//	Load plugins
		self.loadPlugins();

		//	Apply bindings
		bind(tk('body'));
		tk.config.bindFunction = bind;

		tk.iter(initFns, function(f){
			f(self);
		});
	}
	tk.init(init);
}
var core = new CanvasCore();