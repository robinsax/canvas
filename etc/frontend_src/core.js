'use strict';
/*
	The canvas front-end core. Requires toolkit.js.
*/

//	Create the canvas toolkit instance.
var tk = createToolkit({
	debug: '{{ config.debug }}' == 'True'
});

function CanvasCore(){
	/*
		The canvas core interface, assigned to `core` at window scope.
	*/
	var self = this;
	//	Insert configured style properties for reference.
	this.palettes = JSON.parse('{{ config.styling.palettes|json(camelize_keys=True) }}');
	this.breakpoints = JSON.parse('{{ config.styling.breakpoints|json }}');

	//	The current route and query string.
	this.route = null;
	this.query = {};
	//	The meta page and page elements.
	this.metaPage = null;
	this.page = null;

	//	Alias some toolkit properties.
	this.init = tk.init;
	this.debug = tk.config.debug;

	/* ::include storage.js */

	/* -- Plugin interface -- */
	//	Plugin tracking.
	this.plugins = {};
	var unloadedPlugins = [];

	//	Function decorator template.
	function stored(map, func, name){
		if (name === undefined){
			var declaration = tk.functionName(func);
			if (declaration != '<anonymous function>'){
				name = declaration[1];
			}
			else {
				func.__targetContainer__ = map;
			}
		}
		map[name] = func;
		return func;
	}
	this.action = function(func, name){
		/*
			A function decorator for controller invokable actions.
		*/
		return stored(this.storage.actions, func, name);
	}
	
	this.event = function(func, name){ 
		/*
			A function decorator for DOM-triggered events.
		*/
		return stored(this.storage.events, func, name); 
	}

	this.validator = function(func, name){
		/*
			A function decorator for validator implementations.
		*/
		return stored(this.storage.validators, func, name); 
	}

	this.plugin = function(PluginClass){
		/*
			Register a plugin object constructor. A second positional argument 
			specifies a condition for whether or not the plugin should be 
			instatiated;
			
			* If the condition is omitted, always instantiate the plugin.
			* If the condition is a string, instantiate the plugin if the
				string is equal to the current route.
			* If the condition is a function, invoke the function to determine
				whether to instantiate the plugin.
		*/
		var condition = tk.varg(arguments, 1, true);
		unloadedPlugins.push({
			constructor: PluginClass,
			condition: condition,
			conditionType: tk.typeCheck(condition, 'string', 'function', 'boolean')
		});
	}

	this.loadPlugins = function(){
		/*
			Load all plugins queued for load. Doesn't need to be called by 
			plugin JavaScript under normal circumstances.
		*/
		tk.iter(unloadedPlugins, function(pluginInfo){
			var load = false;
			switch (pluginInfo.conditionType){
				case 0:
					load = self.route == pluginInfo.condition;
					break;
				case 1:
					load = pluginInfo.condition();
					break;
				default:
					break;
			}
			if (!load){
				return;
			}

			//	Create the instance.
			var instance = new pluginInfo.constructor();
			tk.log('Loaded plugin:', instance);
			
			//	Add initialization function.
			if (tk.prop(instance, 'init')){
				self.init(function(){
					instance.init.apply(instance);
				});
			}
			
			//	Catch queued decorations.
			tk.iter(instance, function(property, value){
				if (value == null){
					return;
				}
				if (tk.prop(value, '__targetContainer__')){
					value.__targetContainer__[property] = value;
				}
			});

			self.plugins[instance.name || tk.functionName(pluginInfo.constructor)] = instance;
		});

		//	Reset unloaded.
		unloadedPlugins = [];
	}

	/* ::include forms.js */

	//	Set up flash messages.
	this.flashMessage = null;
	tk.init(function(){
		tk('.flash-message').binding.snap(self, {
			flashMessage: '$e:class(hidden null()):text...(5000)$e:class(hidden true)'
		});
	});

	//	Set up tooltip creation.
	this.tooltip = function(target){
		var pos = target.offset(),
			targetSize = target.size(),
			text = tk.varg(arguments, 2, target.attr('cv-tooltip'));

		var right = pos.x > self.page.size().width/2,
			scroll = this.page.ith(0, false).scrollTop;

		//	TODO: make right do something.

		return self.page.snap('+div.tooltip:class(hidden null()):class(right $r):css(top $t):css(left $l):text', text, {
			r: right,
			t: pos.y - scroll - 10,
			l: pos.x + targetSize.width/2 - 10
		});
	}
	tk.inspection(function(check){
		check.reduce('[cv-tooltip]').iter(function(e){
			var tooltip = null;
			e.on({
				mouseover: function(){
					tooltip = self.tooltip(e);
				},
				mouseout: function(){
					tooltip.remove();
				}
			})
		});
	});

	//	Customize requests.
	this.request = function(){
		var varg = tk.varg.on(arguments);
		return tk.request(varg(0, 'POST'), varg(1, window.location.href));
	}
	tk.request.processor(function(request){
		request.header('X-Canvas-View-Request', '1');
		if (request.fns.success === tk.fn.eatCall){
			//	Add an action check response.
			request.fns.success = function(response){
				if (tk.prop(response, 'data') && tk.prop(response.data, 'action')){
					core.storage.actions[response.data.action](response);
				}
			}
		}
		if (request.fns.failure === tk.fn.eatCall){
			request.fns.failure = function(){
				self.flashMessage = 'An error occured';
			}
		}
	});
	
	/* ::include constructs.js */

	//	Set up event-binding inspection.
	tk.inspection(function(check){
		check.reduce('[cv-event]')
			.on('click', function(e, evt){
				var key = e.attr('cv-event'),
					event = tk.prop(self.storage.events, key, null);
				if (event != null){
					event(e, evt);
				}
				else {
					throw 'No such event: ' + key;
				}
			})
		.back()
		.reduce('.button').classify('open', function(e){
			return e.attr('href') == self.route;
		});
	});
	
	//	Set up core initialization.
	tk.init(function(){
		var body = tk('body');
		//	Parse DOM.
		self.route = body.attr('cv-route');
		self.page = body.children('.page', false);
		self.metaBody = body.children('.meta-body');

		//	Parse query string.
		tk.iter(window.location.search.substring(1).split('&'), function(param){
			param = param.split('=');
			self.query[decodeURIComponent(param[0])] = decodeURIComponent(param[1]);
		});

		//	Load plugins.
		self.loadPlugins();
	});
}
//	Create.
var core = new CanvasCore();
