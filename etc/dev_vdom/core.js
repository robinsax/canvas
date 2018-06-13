var _typeof = typeof Symbol === "function" && typeof Symbol.iterator === "symbol" ? function (obj) { return typeof obj; } : function (obj) { return obj && typeof Symbol === "function" && obj.constructor === Symbol && obj !== Symbol.prototype ? "symbol" : typeof obj; };

var _createClass = function () { function defineProperties(target, props) { for (var i = 0; i < props.length; i++) { var descriptor = props[i]; descriptor.enumerable = descriptor.enumerable || false; descriptor.configurable = true; if ("value" in descriptor) descriptor.writable = true; Object.defineProperty(target, descriptor.key, descriptor); } } return function (Constructor, protoProps, staticProps) { if (protoProps) defineProperties(Constructor.prototype, protoProps); if (staticProps) defineProperties(Constructor, staticProps); return Constructor; }; }();

function _possibleConstructorReturn(self, call) { if (!self) { throw new ReferenceError("this hasn't been initialised - super() hasn't been called"); } return call && (typeof call === "object" || typeof call === "function") ? call : self; }

function _inherits(subClass, superClass) { if (typeof superClass !== "function" && superClass !== null) { throw new TypeError("Super expression must either be null or a function, not " + typeof superClass); } subClass.prototype = Object.create(superClass && superClass.prototype, { constructor: { value: subClass, enumerable: false, writable: true, configurable: true } }); if (superClass) Object.setPrototypeOf ? Object.setPrototypeOf(subClass, superClass) : subClass.__proto__ = superClass; }

function _toConsumableArray(arr) { if (Array.isArray(arr)) { for (var i = 0, arr2 = Array(arr.length); i < arr.length; i++) { arr2[i] = arr[i]; } return arr2; } else { return Array.from(arr); } }

function _classCallCheck(instance, Constructor) { if (!(instance instanceof Constructor)) { throw new TypeError("Cannot call a class as a function"); } }

var VirtualDOMRenderer = function () {
	function VirtualDOMRenderer() {
		_classCallCheck(this, VirtualDOMRenderer);
	}

	_createClass(VirtualDOMRenderer, [{
		key: 'flatten',
		value: function flatten(iterable) {
			while (true) {
				var verifiedFlat = true,
				    pass = [];

				for (var i = 0; i < iterable.length; i++) {
					var item = iterable[i];
					if (item instanceof Array) {
						pass = pass.concat(item);
						verifiedFlat = false;
					} else {
						pass.push(item);
					}
				}

				if (verifiedFlat) return pass;
			}
		}
	}, {
		key: 'diff',
		value: function diff(oldVirtual, newVirtual) {
			return (typeof oldVirtual === 'undefined' ? 'undefined' : _typeof(oldVirtual)) != (typeof newVirtual === 'undefined' ? 'undefined' : _typeof(newVirtual)) || typeof oldVirtual == 'string' && oldNode != newVirtual || oldVirtual.tag != newVirtual.tag || newVirtual.attributes && newVirtual.attributes.forceRender;
		}
	}, {
		key: 'devirtualize',
		value: function devirtualize(virtual) {
			if (!virtual) return document.createTextNode('');
			var sourceView = null;
			if (virtual instanceof viewhost.View) {
				var _virtual;

				sourceView = virtual;
				virtual = typeof virtual.template == 'function' ? (_virtual = virtual).template.apply(_virtual, _toConsumableArray(virtual.getRenderContext())) : virtual.template;
			}

			var el = null;
			if (typeof virtual == 'string' || typeof virtual == 'number') {
				el = document.createTextNode(virtual + '');
			} else if (typeof virtual == 'function') {
				el = this.devirtualize(virtual());
			} else if (virtual instanceof Array) {
				var devirtualized = [];
				for (var i = 0; i < virtual.length; i++) {
					devirtualized.push(this.devirtualize(virtual[i]));
				}
				el = devirtualized;
			} else {
				el = document.createElement(virtual.tag);

				for (var attr in virtual.attributes) {
					var value = virtual.attributes[attr];
					if (attr === 'safeHTML') {
						el.innerHTML = value;
					} else if (attr == 'boundData') {
						el.__data__ = value;
					} else {
						el.setAttribute(attr, value);
					}
				}

				if (virtual.children.length > 0) {
					for (var _i = 0; _i < virtual.children.length; _i++) {
						var childEl = this.devirtualize(virtual.children[_i]);
						if (childEl instanceof Array) {
							for (var j = 0; j < childEl.length; j++) {
								el.appendChild(childEl[j]);
							}
						} else {
							el.appendChild(childEl);
						}
					}
				}
			}

			if (sourceView) sourceView.onRender(el);
			return el;
		}
	}, {
		key: 'updateAttributes',
		value: function updateAttributes(targetEl, oldAttrs, newAttrs) {
			for (var attr in oldAttrs) {
				if (!oldAttrs[attr] || oldAttrs[attr] != newAttrs[attr]) return;

				targetEl.setAttribute(attr, newAttrs[attr]);
			}
			for (var _attr in oldAttrs) {
				if (!newAttrs[_attr]) return;

				targetEl.removeAttribute(_attr);
			}
		}
	}, {
		key: 'update',
		value: function update(parentEl, newVirtual, oldVirtual) {
			var index = arguments.length > 3 && arguments[3] !== undefined ? arguments[3] : 0;

			if (!oldVirtual) {
				parentEl.appendChild(this.devirtualize(newVirtual));
			} else if (!newVirtual) {
				if (parentEl.childNodes[index]) {
					parentEl.removeChild(parentEl.childNodes[index]);
					throw 'x'; //	TODO: What the fuck.
				}
			} else if (this.diff(newVirtual, oldVirtual)) {
				parentEl.replaceChild(this.devirtualize(newVirtual), parent.childNodes[index]);
			} else if (newNode.tag) {
				this.updateAttributes(parent.childNodes[index], newVirtual.attributes, oldVirtual.attributes);

				var maxI = Math.max(newVirtual.children.length, oldVirtual.children.length);

				for (var i = 0; i < maxI; i++) {
					try {
						this.update(parent.childNodes[index], newVirtual.children[i], oldVirtual.children[i], i);
					} catch (ex) {
						if (ex !== 'x') throw ex;
						i--; //	TODO: What the fuck pt. 2.
					}
				}
			}
		}
	}, {
		key: 'element',
		value: function element(tag, attributes) {
			for (var _len = arguments.length, children = Array(_len > 2 ? _len - 2 : 0), _key = 2; _key < _len; _key++) {
				children[_key - 2] = arguments[_key];
			}

			return {
				tag: tag,
				attributes: attributes,
				children: children
			};
		}
	}, {
		key: 'render',
		value: function render(renderable) {
			var parentEl = document.createDocumentFragment();
			this.update(parentEl, renderable, null);
			return parentEl.children[0];
		}
	}]);

	return VirtualDOMRenderer;
}();

var ResourceManager = function () {
	function ResourceManager() {
		_classCallCheck(this, ResourceManager);
	}

	_createClass(ResourceManager, [{
		key: 'export',
		value: function _export(moduleName, exportMap) {
			window[moduleName] = exportMap;
		}
	}, {
		key: 'include',
		value: function include(stylesheet) {
			var importHost = document.createElement('link');
			importHost.setAttribute('type', 'text/css');
			importHost.setAttribute('rel', 'stylesheet');
			importHost.setAttribute('href', stylesheet.replace('.', '/') + '.css');
			document.getElementsByTagName('head')[0].appendChild(importHost);
		}
	}, {
		key: 'import',
		value: function _import(moduleName, callback) {
			if (window[moduleName]) {
				callback();
				return;
			}

			var importHost = document.createElement('script');
			importHost.type = 'text/javascript';
			if (importHost.readyState) {
				importHost.onreadystatechange = function () {
					if (!(importHost.readyState === 'loaded' || importHost.readyState == 'complete')) return;

					importHost.onreadystatechange = null;
					callback();
				};
			} else {
				importHost.onload = callback;
			}

			importHost.setAttribute('src', moduleName.replace('.', '/') + '.js');
			document.getElementsByTagName('head')[0].appendChild(importHost);
		}
	}]);

	return ResourceManager;
}();

var ViewProvider = function () {
	function ViewProvider() {
		_classCallCheck(this, ViewProvider);

		var RootView = function () {
			function RootView() {
				_classCallCheck(this, RootView);
			}

			_createClass(RootView, [{
				key: 'getRenderContext',
				value: function getRenderContext() {
					return [];
				}
			}, {
				key: 'onRender',
				value: function onRender(el) {}
			}]);

			return RootView;
		}();

		this.View = RootView;
	}

	_createClass(ViewProvider, [{
		key: 'view',
		value: function view(options) {
			var _this2 = this;

			return function (ViewClass) {
				var DerivedViewClass = function (_ViewClass) {
					_inherits(DerivedViewClass, _ViewClass);

					function DerivedViewClass() {
						var _ref;

						_classCallCheck(this, DerivedViewClass);

						for (var _len2 = arguments.length, args = Array(_len2), _key2 = 0; _key2 < _len2; _key2++) {
							args[_key2] = arguments[_key2];
						}

						var _this = _possibleConstructorReturn(this, (_ref = DerivedViewClass.__proto__ || Object.getPrototypeOf(DerivedViewClass)).call.apply(_ref, [this].concat(args)));

						_this.template = options.template;
						return _this;
					}

					return DerivedViewClass;
				}(ViewClass);

				var Current = DerivedViewClass.prototype;
				while (Object.getPrototypeOf(Current) !== Object.prototype) {
					Current = Object.getPrototypeOf(Current);
					if (Current === _this2.View.prototype) return;
				}

				Object.setPrototypeOf(Current, _this2.View.prototype);

				return DerivedViewClass;
			};
		}
	}]);

	return ViewProvider;
}();

var Utils = function () {
	function Utils() {
		_classCallCheck(this, Utils);
	}

	_createClass(Utils, [{
		key: 'comp',
		value: function comp(iterable) {
			var transform = arguments.length > 1 && arguments[1] !== undefined ? arguments[1] : function (x) {
				return x;
			};

			var result = [];
			for (var i = 0; i < iterable.length; i++) {
				var item = transform(iterable[i], i);
				if (item.tag !== undefined && item.attributes !== undefined && item.children !== undefined) {
					item.attributes = result.attributes || {};
					item.attributes.boundData = iterable[i];
				}
				result.push(item);
			}
			return result;
		}
	}]);

	return Utils;
}();

var renderer = new VirtualDOMRenderer();
var viewhost = new ViewProvider();
var utils = new Utils();
var resources = new ResourceManager();