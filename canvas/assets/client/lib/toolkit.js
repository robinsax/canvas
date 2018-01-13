/*
	Return an initialized `Toolkit` object.

	No initialization is performed until this function
	is called, meaning you can include `toolkit.js` on
	pages where it isn't used with minimal performance 
	and space cost.

	The remainder of this documentation assumes this object
	has been canonically instantiated as follows;
	```
	var tk = createToolkit({
		debug: True
	});
	```
	::object
	::argspec config
	:config (Optional, default '.tk-templates') A configuration 
		object containing zero or more of the following configurable 
		values:
		* `templateContainer` A selector for the element
			containing your mapping templates
		* `debug` The debug flag, enabling or disabling
			logging via `Toolkit.debug()` and `ToolkitInstance.debug()`
		* `logElement` A selector for a DOM element to append logging to
*/
function createToolkit(){
	'use strict';
	//	Polyfill Element.matches for IE 7-
	if (!Element.prototype.matches){
		Element.prototype.matches = Element.prototype.msMatchesSelector;
	}
	//	Placeholder Window for non-browser environs
	if (!Window){
		var Window = function(){};
	}

	//	Load configuration
	var config = {
		templateContainer: '.tk-templates',
		dataPrefix: 'tk',
		globalTemplateFunctions: {}, 
		bindFunction: function(){},
		debug: false
	};
	if (arguments.length > 0){
		var ovr = arguments[0];
		for (var entry in ovr){
			config[entry] = ovr[entry];
		}
	}

	//	Define attribute names
	function makeDefault(ext){ return config.dataPrefix + '-' + ext; }
	var attrNames = {
		bind: makeDefault('bind'),
		onto: makeDefault('onto'),
		viewFn: makeDefault('view-fn'),
		src: makeDefault('src'),
		callback: makeDefault('callback'),
		event: makeDefault('event'),
		on: makeDefault('on'),
		template: makeDefault('template')
	}
	
	/* ## Debug logging (Extra) */
	/*
		Log values for debugging.

		::argspec item1, ..., itemN
	*/
	function debug(){
		if (config.debug){
			console.log.apply(null, arguments);
		}
	}
	/*
		Return the current time in milliseconds.
	*/
	debug.millis = function(){
		var d = new Date();
		return d.getTime();
	}

	/* ## Basic utilities */
	/*
		Iterate an Array or Object, calling a function
		for each (Object, index) or (property name,
		property value) pair, respectively.

		::usage
		```
		var a = ['a', 'b'];
		tk.debug('iter() on Array');
		tk.iter(o, tk.debug);
		
		tk.debug('iter() on Object');
		var o = {
			a: 1,
			b: 2
		};
		tk.iter(o, tk.debug);

		tk.debug('Stopping iter()');
		tk.iter(o, function(propName){
			if (propName == 'a'){
				tk.debug('I'm stopping');
				return;
			}
		})
		```

		::argspec target, func
		:target The Array or Object to iterate
		:func The function to call at each iteration
	*/
	function iter(t, fn){
		switch (typeCheck(t, [Array, 'object', 'number'])){
			case 0:
				for (var i = 0; i < t.length; i++){
					if (fn(t[i], i) === false){
						break;
					}
				}
				return;
			case 1:
				for (var k in t){
					if (fn(k, t[k]) === false){
						break;
					}
				}
				return;
			case 2:
				for (var i = 0; i < t; i++){
					if (fn(i) === false){
						break;
					}
				}
				return;
		}
	}

	/*
		Return whether or not an object has the 
		given property, or pass a third parameter, `default`
		to retrieve the value of that property, returning 
		the default if it isn't present.

		::usage
		```
		var o = {
			a: 1
		};
		var hasA = tk.prop(o, 'a');
		tk.debug('o has property a:', hasA);

		var a = tk.prop(o, 'a', 0);
		tk.debug('o.a = ', a);

		var b = tk.prop(o, 'b', 0);
		tk.debug('o.b defaulted to ', b);
		```

		::argspec object, propertyName, default
		:object The object to check for the given
			property
		:propertyName The name of the property to
			check for
		:default (Optional) A default value to return if 
			the property isn't present
	*/
	function prop(o, p){
		var h = o.hasOwnProperty(p);
		if (arguments.length == 2){
			return h;
		}
		return h ? o[p] : arguments[2];
	}

	/*	
		Return a version of `prop()` bound to the
		given object.
	*/
	prop.on = function(o){
		return function(p){
			if (arguments.length == 2){
				return prop(o, p, arguments[1]);
			}
			return prop(o, p);
		}
	}

	/*
		Call a function later.

		::argspec func, milliseconds, initial
		:func The function to call
		:milliseconds The timeout before the function is
			called, in milliseconds
		:initial Whether to call the function now, too
	*/
	function defer(fn, t){
		setTimeout(fn, t);
		if (varg(arguments, 2, false)){
			fn();
		}
	}

	//	TODO: Doc.
	function repeat(fn, t){
		var i = setInterval(fn, t);
		if (varg(arguments, 2, false)){
			fn();
		}
		return {
			stop: function(){
				clearInterval(i);
			}
		}
	}

	/* ## Variable argument utilities (Extra) */
	/*
		Return the argument at index `i` or a default
		value if there are fewer than `i + 1` arguments.

		::argspec args, i, default, defaultOnNull
		:args The `arguments` object
		:i The index of the argument to (*maybe*)
			retrieve
		:default The default value to return if there
			are fewer than `i + 1` arguments
		:defaultOnNull (Optional, default `false`) Whether the 
			value of the argument at index `i` being `null` 
			should cause this function to return `default`
	*/
	function varg(a, i, d){
		if (a.length > i){
			if (arguments.length > 3 && arguments[3] && a[i] == null){
				//	4th arguments says you want default for null
				return d;
			}
			return a[i];
		}
		return d;
	}
	/*
		Return a version of `varg()` bound to the given
		arguments list, to be used like `varg()`, less
		the first positional argument.

		::argspec args
		:args The arguments list to create a bound version
			of `varg()` on
	*/
	varg.on = function(a){
		return function(i, d){
			return varg(a, i, d, varg(arguments, 2, false));
		}
	}

	/*
		Check the type of an object against a type or 
		list of types, throwing a `TypeError` if the
		check fails, and otherwise returning the
		index of the type for which the check succeeded.

		`types` can contain any combination of:
		* Type strings (e.g. `'number'`, `'function'`, etc.)
		* Constructors (e.g. Array, Element, etc.)
		* `null`

		::argspec object, types
		:object The object to check the type of
		:types The type, or list of types, against
			which to check the object
	*/
	function typeCheck(o, types){
		if (!(types instanceof Array)){
			types = [types];
		}
		var m = -1;
		for (var i = 0; i < types.length; i++){
			var c = types[i];
			if (c == null) {
				//	Null check
				if (o == null){
					m = i;
					break;
				}
			}
			else if (typeof o == c){
				//	Typeof check
				m = i;
				break;
			}
			else {
				//	Class check
				try {
					if (o instanceof c){
						m = i;
						break;
					}
				}
				catch (e){}
			}
		}
		if (m == -1){
			throw new TypeError('Incorrect parameter type ' + (typeof param) + ' (expected one of ' + types + ')');
		}
		return m;
	}

	/*
		Resolve a potentially functional value.

		If `target` is a function, call it and pass it
		the remainder of the parameters passed to this
		function, then return the result.

		Otherwise, return `target`.

		::argspec target, makeTks
		:target The value to resolve
		:makeTks (Optional, default `true`) Whether to create 
			`ToolkitInstance`s for all `Element` arguments
	*/
	function resolve(t){
		if (typeof t == 'function'){
			var args = [].slice.call(arguments);
			args.splice(0, 1);
			if (varg(arguments, 1, true)){
				for (var i = 0; i < args.length; i++){
					if (args[i] instanceof Element){
						args[i] = new ToolkitInstance(args[i]);
					}
				}
			}
			return t.apply(null, args);
		}
		else {
			return t;
		}
	}
	
	/* ## The `ToolkitInstance` object */
	/*	
		The `ToolkitInstance` object holds a set
		of selected DOM `Node`s and provides methods
		for modifying the properties of its members.

		The set of elements selected by a
		`ToolkitInstance` is, for all intents and
		purposes, immutable.

		`ToolkitInstance`s can be conviently instantiated
		by calling the function returned by `createToolkit()`.
		For example;
		```
		var foobars = tk('.foobar');
		```

		Aside from the methods below, `ToolkitInstance`s
		have the properties `length` and `empty` for
		inspecting the cardinality of the set of selected
		elements.

		::object
		::argspec selection
		:selection An `Element`, `Array`, selector `string`, 
			or `Window`
	*/
	function ToolkitInstance(o){
		var self = this;
		
		//	Resolve the selection
		this.set = (function(){
			if (o instanceof ToolkitInstance){
				o = o.set.splice();
			}
			switch (typeCheck(o, [Element, Window, Array, 'string'])) {
				case 0:
				case 1: return [o];
				case 2:
					for (var i = 0; i < o.length; i++){
						var e = o[i];
						if (e instanceof ToolkitInstance){
							o[i] = e.set[0];
						}
					}
					return o;
				case 3: return document.querySelectorAll(o);
			}
		})();
		//	Parent for back()
		this.backP = varg(arguments, 1, null);
		//	Cardinality properties
		this.length = this.set.length;
		this.empty = this.length == 0;
		
		/* ## In-chain debugging (Extra) */

		/*	
			Print a labeled debug statement while chaining.
			For example;
			```
			tk('.foo').debug('Before reduction')
				.reduce('.bar').debug('After reduction');
			```
			::argspec label
			:label (Optional, default `'Debug'`) The label to use
		*/
		this.debug = function(){
			console.log(varg(arguments, 0, 'Debug') + ':', this);
			return this;
		}

		/* ## Selection modifiers and chaining */

		/*
			Move backwards once in the chain (i.e., return
			the `ToolkitInstance` that created this one).

			For example:
			```
			tk('.foo').reduce('.bar')
				.debug('Selecting all foos that are bars')
				.back().debug('Selecting all foos');
			```
		*/
		this.back = function(){
			if (this.backP == null){
				throw new ChainingError('Called back() without parent');
			}
			return this.backP;
		}

		/*
			Return a new `ToolkitInstance` selecting
			the same set, but in reverse order.
		*/
		this.reverse = function(){
			var ns = this.set.slice();
			ns.reverse();
			return new ToolkitInstance(ns, this);
		}

		/*	
			Return a new `ToolkitInstance` selecting the 
			`i`th selected element, or the `i`th selected
			element itself.
			
			::argspec i, returnElem
			:returnElem (Optional, default `false`) Whether to
				return the `Element` rather than a `ToolkitInstance`
				selecting it.
		*/
		this.ith = function(i){
			var w = varg(arguments, 1, false);
			return !w ? new ToolkitInstance(this.set[i], this) : this.set[i];
		}

		/*
			Return a new `ToolkitInstance` selecting all
			element selected elements that match `'selector'`.

			::argspec selector
			:selector (Functional) The selection filter
		*/
		this.reduce = function(s){
			typeCheck(s, ['string', 'function']);
			var ns = [], max = varg(arguments, 1, -1);
			this.iter(function(e, i){
				if (e.is(resolve(s, e, i))){
					ns.push(e);
					if (max >= 0 && ns.length == max){
						return false;
					}
				}
			});
			return new ToolkitInstance(ns, this);
		}

		/*
			Return a new `ToolkitInstance` with an
			expanded set of selected elements.

			::argspec toInclude
			:toInclude An `Array` or `ToolkitInstance`
				with which to extend the selection
		*/
		this.extend = function(o){
			switch (typeCheck(o, [ToolkitInstance, Array])){
				case 0:
					o = o.set;
				case 1:
					var ns = [];
					this.iter(function(e, i){
						ns.push(e);
					}, false);
					for (var i = 0; i < o.length; i++){
						ns.push(o[i]);
					}
					return new ToolkitInstance(ns, this);
			}
		}

		/*
			Return a new `ToolkitInstance` selecting the
			most immediate parent of each element in the
			currently selected set.
		*/
		this.parent = function(){
			return this.parents('*', false);
		}

		/*
			Return a new `ToolkitInstance` selecting all
			parents of the currently selected elements.

			A selector can be used to filter which elements
			are selected.

			::argspec selector, high
			:selector (Optional, functional) A selector to filter on
			:high (Optional, default `true`) Whether to return all
				parents or only immediate ones
		*/
		this.parents = function(){
			var s = arguments.length > 0 ? arguments[0] : null,
				h = arguments.length > 1 ? arguments[1] : true, l = [];
			typeCheck(s, [null, 'string', 'function']);
			typeCheck(h, ['boolean']);
			if (h){
				this.iter(function(e, i){
					var p = e.parentNode;
					while (p !== document){
						if (s == null || p.matches(resolve(s, e, i))){
							l.push(p);
						}
						p = p.parentNode;
					}
				}, false);
			}
			else {
				this.iter(function(e, i){
					var p = e.parentNode;
					if (s == null || p.matches(resolve(s, e, i))){
						l.push(p);
					}
				}, false);
			}
			return new ToolkitInstance(l, this);
		}
		
		/*
			Return a new `ToolkitInstance` selecting all
			the childen of all selected elements.

			A selector can be used to filter which elements
			are selected.

			::argspec selector, deep
			:selector (Optional, functional) A selection filter
			:deep (Optional, default `true`) Whether to return all children
				or only immediate ones
		*/
		this.children = function(){
			//	TODO: Allow children(false) for shallow any
			//	TODO: Vargify
			var l = [], s = arguments.length > 0 ? arguments[0] : '*',
				d = arguments.length > 1 ? arguments[1] : true;
			if (d){
				this.iter(function(e, i){
					var mine = e.querySelectorAll(resolve(s, e, i));
					for (var j = 0; j < mine.length; j++){
						var g = mine[j];
						if (l.indexOf(g) == -1){
							l.push(g);
						}
					}
				}, false);
			}
			else {
				this.iter(function(e, i){
					var mine = e.children;
					for (var j = 0; j < mine.length; j++){
						var c = mine[j];
						if (s == null || c.matches(resolve(s, e, i))){
							l.push(c);
						}
					}
				}, false);
			}
			return new ToolkitInstance(l, this);
		}

		/*
			Deep-copy the first selected element and
			return a `ToolkitInstance` selecting it.

			::firstonly
		*/
		this.copy = function(){
			return new ToolkitInstance(this.set[0].cloneNode(true), this);
		}

		/* ## Inspection */
		/*
			Return:
			* Given an `Element`, whether the selected set
				contains only that element
			* Given an `Array`, whether the array contains all
				elements of the selected set, and vice-versa
			* Given a `ToolkitInstance`, whether it is selecting
				the identical set of elements

			::argspec object
			:object The `Element`, `Array`, or `ToolkitInstance`
				to check for equality against
		*/
		this.equals = function(o){
			switch(typeCheck(o, [Element, Array, ToolkitInstance])){
				case 0:
					return self.length == 1 && self.set[0] == o;
				case 2:
					o = o.set;
				case 1:
					var d = false;
					iter(o, function(e){
						if (self.set.indexOf(e) == -1){
							d = true;
							return false;
						}
					});
					iter(self.set, function(e){
						if (o.indexOf(e) == -1){
							d = true;
							return false;
						}
					})
					return !d && self.length == o.length;
			}
		}

		/*	
			Iterate the currently selected set, passing each
			selected element and its index to a callback (in
			that order).

			Like `Toolkit.iter()`, callbacks can return false
			to stop the loop.

			::argspec func, propagate
			:func The iteration callback
			:propagate (Optional, default `true`) whether to pass 
				elements to the callback as `ToolkitInstance`s 
				instead of `Element`s.
		*/
		this.iter = function(fn){
			var pgt = arguments.length > 1 ? arguments[1] : true;
			for (var i = 0; i < this.set.length; i++){
				var e = this.set[i];
				if (pgt){
					e = new ToolkitInstance(e, this);
				}
				if (fn(e, i) === false){
					break;
				}
			}
			return this;
		}

		/*	
			Return whether all selected elements
			match a selector.
		
			:selector (Functionable) The selector to check
		*/
		this.is = function(selector){
			typeCheck(selector, ['string', 'function']);
			for (var i = 0; i < this.length; i++){
				var e = this.set[i];
				if (!e.matches(resolve(selector, e, i))){
					return false;
				}
			}
			return true;
		}

		/*
			Return the complete list of classes for
			all selected elements.
		*/
		this.classes = function(){
			var all = [];
			this.iter(function(e){
				var mine = e.className.split(/\s+/);
				for (var i = 0; i < mine.length; i++){
					var cls = mine[i];
					if (all.indexOf(cls) == -1){
						all.push(cls);
					}
				}
			}, false);
			return all;
		}

		/*
			Return the value of the first selected
			element if it's an input.
		*/
		this.value = function(){
			if (arguments.length > 0){
				var v = arguments[0];
				this.iter(function(e, i){
					e.value = v;
				}, false);
				return this;
			}
			else {
				if (this.set[0].type == 'checkbox'){
					return this.set[0].checked;
				}
				return this.set[0].value;
			}
		}

		/* ## Inspection *and* modification */
		/*
			Get, set, or modify element attributes.

			### Get
			Return the value of an attribute on the first selected
			element, or `null` if it isn't present.

			### Set
			Set an attribute, or multiple attributes from
			an object by property. Attribute values are functional.
			
			If a single attribute is being set, attribute
			name is functional.
			
			To remove an attribute, pass `null`.

			::usage
			```
			var x = tk('.foobar');
			tk.debug('data-foo of first foobar:', x.attr('data-foo'));

			tk.debug('data-fake of first foobar:', x.attr('data-bar'));
			
			x.attr('data-bar', 'foo');
			x.attr(function(e, i){ return 'data-foo-' + i; }, function(e, i){ return i; });
			x.attr({
				'data-foo': 'bar',
				'data-bar': function(e, i){ return e.attr('data-bar') + x.length - i; }
			});
			```
			
			::softfirstonly
			::argspec attr, value | object
			:attr (Functional) The attribute name
			:value (Optional, functional) The attribute value
			:object The object containing attribute names and values
				as properties
		*/
		this.attr = function(a){
			switch (typeCheck(a, ['string', 'object'])) {
				case 0:
					if (arguments.length > 1){
						var name = a, val = arguments[1];
						switch (typeCheck(val, [null, 'string', 'function'])){
							case 0:
								this.iter(function(e, i){
									e.removeAttribute(name, null);
								}, false);
								break;
							default:
								this.iter(function(e, i){
									e.setAttribute(resolve(name, e, i), resolve(val, e, i));
								}, false);
						}
					}
					else {
						if (this.set[0].hasAttribute(a)){
							return this.set[0].getAttribute(a);
						}
						return null;
					}
					break;
				case 1:
					this.iter(function(e, i){
						for (var name in a){
							e.setAttribute(name, resolve(a[name], e, i));
						}
					}, false);
					break;
			}
			return this;
		}

		/*
			Get computed styles and set element-level styles.
			
			### Get
			Retrieve the computed value of a style for the 
			first selected element.

			### Set
			Set an element-level style for each selected element, or set
			multiple styles from object by property.

			When setting a single style, style name is functional.

			Style value is always functionable.

			::usage
			```
			var x = tk('.foobar');

			x.css('background-color', 'red');
			x.css('background-color', function(e){ 
				return e.is('.cucumber') ? 'green' : 'blue'; 
			});
			x.css(function(e){
				if (e.css('background-color') == 'green'){
					return 'margin-bottom';
				}
				return 'margin-left';
			}, '20px');
			x.css({
				'color': 'red',
				'font-weight': 'bold',
				'font-size': function(e){
					return e.is('.cucumber') ? '10pt' : '20pt';
				}
			});
			```

			::softfirstonly
			::argspec styleName, value | object
			:styleName (functional) The name of the CSS style to set, in either
				*dash-case* or *camelCase*
			:value (Optional, functional) The property value
		*/
		this.css = function(p){
			function applyOne(s, v){
				s = s.replace(/-([a-z])/g, function(g){
					return g[1].toUpperCase();
				});		
				self.iter(function(e, i){
					e.style[s] = resolve(v, e, i);
				}, false);
			}

			switch (typeCheck(p, ['string', 'object'])){
				case 0:
					if (arguments.length > 1){
						//	Set a single style
						applyOne(p, arguments[1]);
					}
					else {
						return window.getComputedStyle(this.set[0]).getPropertyValue(p);
					}
					break;
				case 1:
					for (var s in p){
						applyOne(s, p[s]);
					}
					break;
			}
			return this;
		}

		/*
			Attach a callback to all selected elements.

			The callback will be passed a `ToolkitInstance`
			of the firing element, as well as its index.

			::usage
			```
			var x = tk('.foobar');

			x.on('click', function(e){
				alert('Foo!');
			});

			x.on('mouseover', function(e){
				e.css('background-color', 'green');
			});

			x.on({
				'mouseout': function(e){
					e.css('background-color', 'red');
				},
				'click': function(e){
					e.css('color', 'salmon');
				}
			});
			```

			::argspec event, callback
			:event (Functional) The name of the event to bind
				the callback to
			:callback The callback function to bind
		*/
		this.on = function(a){
			function setOne(evt, fn){
				self.iter(function(e, i){
					var list = prop(e, 'tkEventListeners', null);
					if (list == null){
						list = [];
						e.tkEventListeners = list;
					}
					var add = {
						event: resolve(evt, e, i),
						func: function(g){
							fn(new ToolkitInstance(e), g, i);
						}
					}
					list.push(add)
					e.addEventListener(add.event, add.func);
				}, false);
			}

			switch (typeCheck(a, ['function', 'string', 'object'])){
				case 0:
				case 1:
					setOne(a, arguments[1]);
					break;
				case 2:
					for (var k in a){
						setOne(k, a[k]);
					}
					break;
			}
			return this;
		}

		/*
			Remove all listeners for a given event
			from all selected elements.

			::argspec event
			:event The event to remove listeners for
		*/
		this.off = function(a){
			this.iter(function(e){
				var l = prop(e, 'tkEventListeners', []), r = [];
				iter(l, function(o, i){
					if (o.event == a){
						e.removeEventListener(o.event, o.func);
						r.push(i);
					}
				});
				iter(r, function(i){
					l = l.splice(i, 1);
				});
			}, false);
			return this;
		}

		/*
			Add, remove, or toggle a class, or multiple
			classes by object property.

			`flag` is functional.

			If a single class is being flagged, class
			name if functional.

			Passing a non-negative value as the third parameter,
			`time`, will cause the opposite classification to
			the one performed by this function to occur after 
			`time` milliseconds.

			*Please contribute on GitHub to help that sentence*.

			::usage
			```
			tk('.foo').classify('hot', function(e){
				return e.is('.bar');
			}, 500);
			```

			::argspec cls, flag, time | obj
			:cls The class name
			:flag (Optional, functional, default `true`) Whether
				to add or remove the class
			:time (Optional, functional, default `-1`) The deferred
				reversal parameter
		*/
		this.classify = function(a){
			function classifyOne(cls, f, t){
				var sel = '.' + cls, add = ' ' + cls;
				if (f == 'toggle'){
					//	Special second parameter option
					f = function(e, i){
						return !e.is(sel);
					}
				}
				self.iter(function(e, i){
					var g = resolve(f, e, i);
					if (g){
						//	Add
						if (!e.is(sel)){
							e.set[0].className += add
						}
					}
					else {
						//	Remove
						if (e.is(sel)){
							var classes = e.classes();
							classes.splice(classes.indexOf(cls), 1);
							e.set[0].className = classes.join(' ');
						}
					}
					var mt = resolve(t, e, i);
					if (mt >= 0){
						defer(function(){
							classifyOne(cls, !g, -1);
						}, mt);
					}
				});
			}

			switch (typeCheck(a, ['string', 'object'])){
				case 0:
					//	Set single
					classifyOne(a, varg(arguments, 1, true), varg(arguments, 2, -1));
					break;
				case 1:
					for (var cls in a){
						classifyOne(cls, a[cls]);
					}
					break;
			}
			return this;
		}

		/*
			Remove all currently selected elements from the
			DOM (they remain selected).
		*/
		this.remove = function(){
			this.iter(function(e){
				if (e.parentNode != null){
					e.parentNode.removeChild(e);
				}
			}, false);
			return this;
		}

		/*
			Append an element to the first matched
			element. If passed a `ToolkitInstance`,
			each of its selected elements are appended.

			Returns a new `ToolkitInstance` selecting
			all appended elements.
			
			::firstonly
			::argspec element
			:element The element or `ToolkitInstance` to append
		*/
		this.append = function(e){
			switch (typeCheck(e, [Array, ToolkitInstance, Element])){
				case 0:
					//	TODO: Efficiency
					var set = [];
					iter(e, function(g){
						var tki = self.append(g);
						tki.iter(function(h){
							set.push(h.set[0]);
						});
					});
					return new ToolkitInstance(set, this);
				case 1:
					e.iter(function(g){
						g.remove();
						self.set[0].appendChild(g.set[0]);
						config.bindFunction(g);
					});
					e.backP = this;
					return e;
				case 2:
					self.set[0].appendChild(e);
					config.bindFunction(e);
					return new ToolkitInstance(e, this);
			}
		}

		/*
			Prepend an element to the first matched
			element. If passed a `ToolkitInstance`,
			each of its selected elements are prepended.

			Returns a new `ToolkitInstance` selecting
			all prepended elements.
		
			::firstonly
			::argspec element
			:element The element or `ToolkitInstance` to append
		*/
		this.prepend = function(e){
			switch (typeCheck(e, [Array, ToolkitInstance, Element])){
				case 0:
					//	TODO: Efficiency
					var set = [];
					e = e.splice(0).reverse();
					iter(e, function(g){
						var tki = self.prepend(g);
						tki.iter(function(h){
							set.push(h.set[0]);
						});
					});
					return new ToolkitInstance(set, this);
				case 1:
					e.reverse().iter(function(g){
						g.remove();
						self.set[0].insertBefore(g.set[0], self.set[0].firstChild);
						config.bindFunction(g);
					});
					e.backP = this;
					return e;
				case 2:
					self.set[0].insertBefore(e, this.set[0].firstChild);
					config.bindFunction(e);
					return new ToolkitInstance(e, this);
			}
		}

		//	TODO: Doc
		this.tag = function(){
			return this.set[0].tagName;
		}

		//	TODO: Doc and move
		this.next = function(){
			var n = this.set[0].nextElementSibling;
			if (n == null){
				n = [];
			}
			return new ToolkitInstance(n, this);
		}

		//	TODO: Doc and move
		this.prev = function(){
			var n = this.set[0].previousElementSibling;
			if (n == null){
				n = [];
			}
			return new ToolkitInstance(n, this);
		}

		/*
			Get the HTML content of the first selected
			element, or set the HTML content of each selected
			element.

			::softfirstonly
			::argspec html
			:html (Optional, functional) The HTML to set
		*/
		this.html = function(){
			if (arguments.length > 0){
				var h = arguments[0];
				this.iter(function(e, i){
					e.innerHTML = resolve(h, e, i);
				}, false);
				return this;
			}
			else {
				return this.set[0].innerHTML;
			}
		}

		/*
			Get the text content of the first selected
			element, or set the text content of each selected
			element.
			
			::softfirstonly
			::argspec text
			:text (Optional, functional) The text to set
		*/
		this.text = function(){
			if (arguments.length > 0){
				var t = arguments[0];
				this.iter(function(e, i){
					e.textContent = resolve(t, e, i);
				}, false);
				return this;
			}
			else {
				return this.set[0].textContent;
			}
		}

		/*
			Select the first selected element if
			it's an input.

			::firstonly
		*/
		this.select = function(){
			this.set[0].select();
			return this;
		}

		/* ## Layout calculation */
		/*
			Return the (`x`, `y`) offset within the document 
			of the first selected element.

			::firstonly
		*/
		this.offset = function(){
			var x = 0, y = 0, e = this.set[0];
			while (e != null){
				x += e.offsetLeft;
				y += e.offsetTop;
				e = e.offsetParent;
			}
			return {x: x, y: y};
		}

		/*
			Return the (`width`, `height`) size of the `content-box`
			of the first selected element.

			::firstonly
			::argspec outer
			:outer (Optional, default `false`) Whether to include `border`
				`margin` and `padding` in the returned size.
		*/
		this.size = function(){
			var e = this.set[0];
			var box = e.getBoundingClientRect();
			var size = {width: box.width, height: box.height};
			if (varg(arguments, 0, false)){
				var style = window.getComputedStyle(e, null);
				//	Add margin
				size.width 
					+= style.getPropertyValue('margin-left') 
					+ style.getPropertyValue('margin-right');
				size.height 
					+= style.getPropertyValue('margin-top') 
					+ style.getPropertyValue('margin-bottom');
				if (style.getPropertyValue('box-sizing') == 'border-box'){
					//	Add padding and TODO: border
					size.width 
						+= style.getPropertyValue('padding-left') 
						+ style.getPropertyValue('padding-right');
					size.height 
						+= style.getPropertyValue('padding-top') 
						+ style.getPropertyValue('padding-bottom');
				}
			}
			return size;
		}
	}

	/* ## Other objects (Extras) */
	/*
		An exception thrown when incorrect chaining occurs 
		(e.g., `back()` is called on a `ToolkitInstance` with
		no parent).

		::object
		:message The exception message
	*/
	function ChainingError(message){
		this.message = message
	}

	/*
		An exception throw when invalid binding parameters
		are parsed.
		
		::object
		:message The exception message
	*/
	function BindParameterError(message){
		this.message = message;
	}

	/*
		The object used internally to live-map a data 
		`Object` to a templated `Element`.

		::internal
		::object
	*/
	function MappedObject(obj, node, parent){
		var self = this;
		var funcs = parent._funcs; // TODO: Remove

		var props = Object.getOwnPropertyNames(obj),
			subtemplates = {};
		this.node = node;
		
		/*
			Remove this object from its parent array.
		*/
		this.remove = function(){
			parent.remove(this, true);
		}

		/*
			Return an unmapped, JSON-serializable copy
			of the mapped data in its current state.
		*/
		this.extract = function(){
			var d = {};
			//	Collect all original properties
			iter(props, function(n, i){
				var v = self[n];
				if (v instanceof MappedArray){
					//	Extract subtemplate
					v = v.extract();
				}
				d[n] = v;
			});
			return d;
		}

		var bindings = {};
		//	Binds each properties onto all template
		//	nodes binding to it
		function parseBindings(remove){

			//	Returns all values (w.s. separated)
			//	or the given binding parameter
			function param(e, a){
				var v = e.attr(a);
				if (v != null){
					if (remove){
						e.attr(a, null);
					}
					var found = v.match(/(?:(?:<.*?>)|[^\s]+)(?:\s+|$)/g);
					iter(found, function(s, i){
						if (s.indexOf('<') == 0){
							s = s.substring(1, s.length - 1);
						}
						found[i] = s.trim();
					});
					return found;
				}
				return [];
			}

			node.children('[' + attrNames.bind + ']').iter(function(e, i){
				//	Read binding parameters
				var to = param(e, attrNames.bind),
					onto = param(e, attrNames.onto),
					viewWith = param(e, attrNames.viewFn),
					callback = param(e, attrNames.callback);
				iter(to, function(t, j){
					if (!prop(bindings, t)){
						bindings[t] = [];
					}
					//	Push binding parameters, expanding those
					//	shorter than to to contain defaults
					bindings[t].push({
						e: e,
						onto: varg(onto, j , 'html'),
						viewWith: varg(viewWith, j, '-'),
						callback: varg(callback, j, '-')
					});
				});
			});
		}
		//	Parse bindings initially to see which elements grabbed 
		//	arrays; those need to be subtemplated
		parseBindings(false);

		//	Remove subtemplates now so we dont bind
		//	callbacks on them at this depth, then reparse 
		//	bindings
		//	TODO: More efficient
		iter(bindings, function(a, bound){
			if (obj[a] instanceof Array){
				//	This will bind to array, virtualize
				//	in subtemplates
				iter(bound, function(b){
					subtemplates[a] = b.e.children('*', false).remove();
				});
			}
		});
		//	Reparse bindings, for real this time
		bindings = {};
		parseBindings(true);

		//	Bind generally without worrying about
		//	depth since subtemplates are gone
		node.children('[' + attrNames.src + ']').on('keyup', function(e){
			self[e.attr(attrNames.src)] = e.value();
		});
		node.children('[' + attrNames.event + ']').on(function(e){
			//	Check if target event was specified
			return e.is('[' + attrNames.on + ']') ? e.attr(attrNames.on) : 'click';
		}, function(e, i){
			funcs[e.attr(attrNames.event)](self, e, i);
		});

		//	Realize a property binding
		function applyBind(p){
			//	On value change new value is specified since
			//	it hasn't applied yet
			var value = varg(arguments, 1, self[p]);
			if (value instanceof MappedArray){
				//	TODO: Y? lol
				return;
			}
			var bound = tk.prop(bindings, p, null);
			if (bound == null){
				//	No bindings on this property
				return;
			}
			iter(bound, function(b, i){
				if (value instanceof Array){
					//	Subtemplate
					self[p] = new MappedArray(value, subtemplates[p], b.e, funcs);
				}
				else {
					//	Transform
					var asViewed = value;
					if  (b.viewWith != '-'){
						if (b.viewWith.indexOf('lambda:') > -1){
							//	Evaluate lambda
							var v = value;
							asViewed = eval('(function(){ return ' + b.viewWith.substring(7) + ' })();');
						}
						else {
							asViewed = funcs[b.viewWith](value, p);
						}
					}
					//	Place
					if (b.onto == 'html'){
						b.e.html(asViewed);
					}
					else if (b.onto.indexOf('attr:') > -1){
						b.e.attr(b.onto.substring(5), asViewed);
					}
					else {
						throw new BindParameterError('Invalid bind ' + attrNames.bind + '="' + b.onto + '"');
					}
					//	Callback
					if (b.callback != '-'){
						funcs[b.callback](asViewed);
					}
				}
			});
		}
		//	Create mapping
		iter(props, function(p){
			//	Define property p here
			Object.defineProperty(self, p, (function(iv, p){
				var v = iv;	//	Tightly-scoped value
				return {
					get: function(){
						return v;
					},
					set: function(n){
						if (v instanceof MappedArray){
							//	n is a new one
							v.remove();
						}
						v = n;
						//	Update the view value
						applyBind(p, v);
					}
				}
			})(obj[p], p));
			//	Apply the initial value
			applyBind(p);
		});
	}

	/*
		The object used internally to map an array of `Object`s
		to a template and the array contents to nodes.

		Replicates common array behavior so as not to be 
		transparently different.

		::internal
		::object
	*/
	function MappedArray(ary, template, target, funcs){
		var self = this;

		//	Add global template functions
		iter(config.globalTemplateFunctions, function(n, f){
			if (prop(funcs, n, null) == null){
				funcs[n] = f;
			}
		});

		this.length = 0;
		this._funcs = funcs; // TODO: Remove
		
		//	Create a fake array-index-like property
		function applyIndex(i, iv){
			Object.defineProperty(self, '' + i, (function(){
				var v = iv;
				return {
					get: function(){
						return v;
					},
					set: function(n){
						v = new MappedObject(o, v.node, self);
					},
					//	May need to be deleted when
					//	array contents change
					configurable: true
				}
			})());
		}

		/*
			Set the data being mapped by this `MappedArray`.
			
			Since even single-object mappings are really
			`MappedArray`s, remapping can be applied in any 
			context with this function.
		*/
		this.remap = function(a){
			while (this.length > 0){
				this.remove(0);
			}
			iter(a, function(o){ self.push(o); });
		}

		/*
			Return an unmapped, JSON-serializable copy
			of the mapped data in its current state.
		*/
		this.extract = function(){
			var d = [];
			for (var i = 0; i < this.length; i++){
				var v = this[i];
				if (v instanceof MappedObject){
					v = v.extract();
				}
				d.push(v);
			}
			return d;
		}

		/*
			Add objects to the list and therefore
			mapped `Element`s to the DOM

			::argspec value1, ..., valueN
		*/
		this.push = function(){
			for (var i = 0; i < arguments.length; i++){
				var v = arguments[i];
				var node = template.copy().attr('tk-template', null);
				applyIndex(self.length, new MappedObject(v, node, self));
				self.length++;
				target.append(node);
			}
		}

		/*
			Return the index of the given object
			in this `MappedArray`, or `-1` if it
			isn't present.

			::argspec object
			:object The object to find the index
				of
		*/
		this.indexOf = function(v){
			for (var i = 0; i < this.length; i++){
				if (this[i] == v){
					return i;
				}
			}
			return -1;
		}

		/*
			Remove an object from this `MappedArray`
			by index, or value.

			If no arguments are supplied, the entire 
			`MappedArray` is emptied.

			::argspec toRemove, useValue
			:toRemove (Optional) The index to remove, or
				if `useValue` is `true`, the object
			:useValue (Optional, default `false`) Whether
				to remove by value or index
		*/
		this.remove = function(){
			if (arguments.length > 0){
				var p = arguments[0];
				if (varg(arguments, 1, false)){
					//	Find index for value
					p = this.indexOf(p);
				}
				//	Remove the index
				this[p].node.remove();
				delete this[p];
				//	Shift all proceeding back
				for (var i = p + 1; i < this.length; i++){
					var v = this[i];
					delete this[i];
					applyIndex(i - 1, v);
				}
				//	Shrink
				this.length--;
			}
			else {
				//	Empty self
				while (this.length > 0){
					this.remove(0);
				}
			}
		}

		//	Map initial data
		this.remap(ary);
	}

	/* ## Basic utilities (TODO: Join) */
	/*
		Create an element.

		::name e
		::argspec tag, cls, html, attrs
		:tag (Optional, default `'div'`) The tag name of the element
		:cls (Optional) The class attribute of the element
		:html (Optional) The html content of the element
		:attrs (Optional) An object containing attributes to be set
			on the element by property name
	*/
	function createElement(){
		var v = varg.on(arguments);
		var e = document.createElement(v(0, 'div'));
		e.className = v(1, '', true);
		e.innerHTML = v(2, '', true);
		iter(v(3, {}), function(a, v){
			e.setAttribute(a, v);
		});
		return new ToolkitInstance(e);
	}

	var processors = [];
	/*
		Send a JSON AJAX request.

		::argspec url, method, data, success, failure
		:url The URL to send the request to
		:method (Default `POST`) The request method
		:data The object to serialize into JSON for the
			request body
		:success A callback on response. Passed the response
			JSON and the response status code
		:failure (Optional, default `success`) A seperate callback
			for if an error status is returned
	*/
	function request(url, method, data, success){
		var failure = varg(arguments, 4, success);
		var method = method.toUpperCase();

		//	Just in case
		if (data instanceof MappedObject || data instanceof MappedArray){
			data = data.extract();
		}
		
		var r = new XMLHttpRequest();
		r.onreadystatechange = function(){
			if (this.readyState == 4){
				var c = this.status, d = JSON.parse(this.responseText);
				(c < 400 ? success : failure)(d, c);
			}
		}

		var d;
		if (method == 'GET'){
			url += '?';
			iter(data, function(a, v){
				url += a + '=' + encodeURIComponent(v);
			});
			r.open(method, url, true);
			d = '';
		}
		else if (method == 'POST'){
			r.open('POST', url, true);
			r.setRequestHeader('Content-Type', 'application/json');
			d = JSON.stringify(data);
		}
		else {
			//	TODO: Support more
			throw 'Unsupported method ' + method;
		}
		iter(processors, function(p){
			p(r, d);
		});
		r.send(d);
		//	TODO: Logging here
	}
	/*
		Add a request processor to modify outgoing
		`XMLHTTPRequest`s.
		
		::argspec func
		:func A callback to modify `XMLHTTPRequest`s
			before they are sent
	*/
	request.processor = function(f){
		processors.push(f);
		return tk;
	}

	var templates = {};
	/*
		Create an return a live mapping between `data`,
		and it's imposition on `template`, inserted as
		children of `target`.

		TODO: Better doc.
	*/
	function map(data, template, target){
		var t = typeof data;
		if (t == 'string' || t == 'number' || t == 'boolean'){
			return data;
		}
		var wrap = !(data instanceof Array);
		if (wrap){
			data = [data];
		}
		var m = new MappedArray(data, templates[template], 
				target, varg(arguments, 3, {}));
		return wrap ? m[0] : m;
	}

	var initFns = [];
	/*
		Add a function to be called when the DOM
		content is loaded.

		::argspec func
		:func The function to call
	*/
	function init(f){
		initFns.push(f);
		return tk;
	}

	var tk = function(obj){
		return new ToolkitInstance(obj);
	}
	//	Populate the object
	tk.config = config;
	tk.prop = prop;
	tk.debug = debug;
	tk.varg = varg;
	tk.defer = defer;
	tk.repeat = repeat;
	tk.iter = iter;
	tk.e = createElement;
	tk.request = request;
	tk.map = map;
	tk.templates = templates;
	tk.init = init;
	tk.typeCheck = typeCheck;
	tk.attrNames = attrNames;
	tk.types = {
		ToolkitInstance: ToolkitInstance,
		MappedObject: MappedObject,
		MappedArray: MappedArray,
		ChainingError: ChainingError
	}

	function doInit(){
		//	Remove and map templates
		var container = tk(config.templateContainer).remove();
		container.children('[' + attrNames.template + ']', false)
			.iter(function(e){
				templates[e.attr(attrNames.template)] = e;
			}).attr(attrNames.template, null);
		debug('Loaded templates:', templates);
		
		//	Call init. functions
		iter(initFns, function(f){
			f();
		});
	}
	
	//	Initialize or wait
	if (/complete|loaded|interactive/.test(document.readyState)){
		doInit();
	}
	else {
		if (window){
			window.addEventListener('DOMContentLoaded', doInit);
		}
	}
	return tk;
}