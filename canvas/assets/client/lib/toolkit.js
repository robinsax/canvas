/*
toolkit.js

Author: Robin Saxifrage
License: Apache 2.0
*/
'use strict';

var _typeof = typeof Symbol === "function" && typeof Symbol.iterator === "symbol" ? function (obj) { return typeof obj; } : function (obj) { return obj && typeof Symbol === "function" && obj.constructor === Symbol && obj !== Symbol.prototype ? "symbol" : typeof obj; };

var _createClass = function () { function defineProperties(target, props) { for (var i = 0; i < props.length; i++) { var descriptor = props[i]; descriptor.enumerable = descriptor.enumerable || false; descriptor.configurable = true; if ("value" in descriptor) descriptor.writable = true; Object.defineProperty(target, descriptor.key, descriptor); } } return function (Constructor, protoProps, staticProps) { if (protoProps) defineProperties(Constructor.prototype, protoProps); if (staticProps) defineProperties(Constructor, staticProps); return Constructor; }; }();

function _classCallCheck(instance, Constructor) { if (!(instance instanceof Constructor)) { throw new TypeError("Cannot call a class as a function"); } }

(function () {
  var Request,
      Toolkit,
      ToolkitAListener,
      ToolkitGuts,
      ToolkitPListener,
      ToolkitSelection,
      ToolkitTemplate,
      _Listeners,
      _RequestModule,
      _SelectionModule,
      _Templates,
      _Toolkit,
      _sentinel,
      callable,
      guts,
      toolkit,
      indexOf = [].indexOf;

  _sentinel = {};

  callable = function callable(Class) {
    return function () {
      var func, inst, j, len, name, names, obj;
      //	Create an instance.
      inst = new Class();
      //	Create a function that invokes _call()
      func = function func() {
        for (var _len = arguments.length, args = Array(_len), _key = 0; _key < _len; _key++) {
          args[_key] = arguments[_key];
        }

        return inst._call.apply(this, args);
      };

      //	Copy the properties of the instance onto the function.
      obj = inst;
      while (true) {
        names = Object.getOwnPropertyNames(obj);
        for (j = 0, len = names.length; j < len; j++) {
          name = names[j];
          if (typeof obj[name] === 'function') {
            func[name] = obj[name];
          } else {
            Object.defineProperty(func, name, Object.getOwnPropertyDescriptor(obj, name));
          }
        }
        if (!(obj = Object.getPrototypeOf(obj))) {
          break;
        }
      }

      //	Return the function.
      return func;
    };
  };

  //	The protected internals of the base Toolkit instance. Nothing within this
  //	object should be considered exposed.
  ToolkitGuts = function () {
    function ToolkitGuts() {
      _classCallCheck(this, ToolkitGuts);

      this.initFunctions = [];
      this.inspectionFunctions = [];
      this.modules = [];
      return;
    }

    _createClass(ToolkitGuts, [{
      key: 'attach',
      value: function attach(Module) {
        this.modules.push(Module);
        return this;
      }
    }, {
      key: 'onto',
      value: function onto(tk) {
        var Module, inst, j, len, ref;
        ref = this.modules;
        for (j = 0, len = ref.length; j < len; j++) {
          Module = ref[j];
          inst = new Module(tk);
          if (inst.called) {
            tk[inst.called] = inst;
          }
        }
        return this;
      }
    }, {
      key: 'init',
      value: function init() {
        var f, j, len, ref;
        ref = this.initFunctions;
        for (j = 0, len = ref.length; j < len; j++) {
          f = ref[j];
          f();
        }
        return this;
      }
    }, {
      key: 'inspect',
      value: function inspect(check) {
        var f, j, len, ref;
        ref = this.inspectionFunctions;
        for (j = 0, len = ref.length; j < len; j++) {
          f = ref[j];
          f(check);
        }
        return this;
      }
    }]);

    return ToolkitGuts;
  }();

  //	Create the guts.
  guts = new ToolkitGuts();

  Request = function () {
    function Request(tk1, method, url) {
      _classCallCheck(this, Request);

      this.tk = tk1;
      this.info = {
        method: method,
        url: url,
        success: function success() {
          return {};
        },
        failure: function failure() {
          return {};
        },
        query: {},
        headers: {},
        body: null
      };
    }

    _createClass(Request, [{
      key: 'success',
      value: function success(callback) {
        this.info.success = callback;
        return this;
      }
    }, {
      key: 'failure',
      value: function failure(callback) {
        this.info.failure = callback;
        return this;
      }
    }, {
      key: 'json',
      value: function json(data) {
        this.info.headers['Content-Type'] = 'application/json';
        this.info.body = this.tk.unbound(data);
        return this;
      }
    }, {
      key: 'data',
      value: function data(_data) {
        var mimetype = arguments.length > 1 && arguments[1] !== undefined ? arguments[1] : 'text/plain';

        this.info.headers['Content-Type'] = mimetype;
        this.info.body = _data;
        return this;
      }
    }, {
      key: 'header',
      value: function header(key, value) {
        this.info.headers[key] = value;
        return this;
      }
    }, {
      key: 'query',
      value: function query(map) {
        this.info.query = map;
        return this;
      }

      //	TODO: More mimetype support.

    }, {
      key: 'send',
      value: function send() {
        var _this = this;

        var fullURL, key, mimetypeOut, processResponse, queryKeys, queryStatements, ref, serializedBody, value, xhr;
        //	Declare response callback.
        processResponse = function processResponse(xhr) {
          var data, mimetype, status;
          status = xhr.status;
          mimetype = xhr.getResponseHeader('Content-Type');
          data = xhr.responseText;
          switch (mimetype) {
            case 'application/json':
              data = JSON.parse(data);
          }
          _this.tk.log('Recieved ' + status + ' (' + _this.info.method + ', ' + _this.info.url + ')');
          return (status < 400 ? _this.info.success : _this.info.failure)(data, status);
        };

        //	Prepare data.
        fullURL = this.info.url;
        serializedBody = '';
        queryKeys = Object.keys(this.info.query);
        if (queryKeys > 0) {
          queryStatements = function () {
            var j, len, results;
            results = [];
            for (j = 0, len = queryKeys.length; j < len; j++) {
              key = queryKeys[j];
              results.push(key + '=' + encodeURIComponent(this.info.query[key]));
            }
            return results;
          }.call(this);
          fullURL += '?' + queryStatements.join('&');
        }
        if (this.info.body) {
          mimetypeOut = this.info.headers['Content-Type'];
          switch (mimetypeOut) {
            case 'application/json':
              serializedBody = JSON.stringify(this.info.body);
              break;
            default:
              throw 'Unknown outgoing mimetype ' + mimetypeOut;
          }
        }
        //	Prepare an XHR.
        xhr = new XMLHttpRequest();
        xhr.onreadystatechange = function () {
          if (this.readyState === 4) {
            return processResponse(this);
          }
        };
        xhr.open(this.info.method, fullURL, true);
        ref = this.info.headers;
        for (key in ref) {
          value = ref[key];
          xhr.setRequestHeader(key, value);
        }
        xhr.send(serializedBody);
        return this.tk.log('Sent (' + this.info.method + ', ' + this.info.url + ')', this.info.body);
      }
    }]);

    return Request;
  }();

  guts.attach(callable(_RequestModule = function () {
    function _RequestModule(tk1) {
      _classCallCheck(this, _RequestModule);

      this.tk = tk1;
      this.called = 'request';
    }

    _createClass(_RequestModule, [{
      key: '_call',
      value: function _call(method, url) {
        return new Request(this, method, url);
      }
    }]);

    return _RequestModule;
  }()));

  ToolkitSelection = function () {
    var ToolkitSelection = function () {
      _createClass(ToolkitSelection, null, [{
        key: 'clean',
        value: function clean(set) {
          var clean, item, j, len;
          if (set instanceof Node) {
            return [set];
          } else if (set instanceof ToolkitSelection) {
            set = set.set;
          }
          clean = [];
          for (j = 0, len = set.length; j < len; j++) {
            item = set[j];
            if (item instanceof ToolkitSelection) {
              clean = clean.concat(item.set);
            } else {
              clean.push(item);
            }
          }
          return clean;
        }
      }]);

      function ToolkitSelection(selection, parent1) {
        _classCallCheck(this, ToolkitSelection);

        var item, j, len;
        this.parent = parent1;
        //	Resolve the selection set.
        if (selection instanceof ToolkitSelection) {
          this.set = selection.set.slice();
        } else if (selection instanceof Element || selection instanceof Node || selection instanceof Window) {
          this.set = [selection];
        } else if (selection instanceof NodeList || selection instanceof Array) {
          this.set = [];
          for (j = 0, len = selection.length; j < len; j++) {
            item = selection[j];
            this.set = this.set.concat(ToolkitSelection.clean(item));
          }
        } else if (typeof selection === 'string') {
          this.set = ToolkitSelection.tk.config.root.querySelectorAll(selection);
        } else {
          throw 'Illegal selection: ' + selection;
        }
        this.length = this.set.length;
        this.empty = this.length === 0;
      }

      _createClass(ToolkitSelection, [{
        key: 'back',
        value: function back() {
          if (!this.parent) {
            throw 'Illegal back';
          }
          return this.parent;
        }
      }, {
        key: 'ith',
        value: function ith(i) {
          var wrap = arguments.length > 1 && arguments[1] !== undefined ? arguments[1] : true;

          if (i < 0 || i > this.length) {
            throw 'Out of bounds: ' + i;
          }
          if (wrap) {
            return new ToolkitSelection(this.set[i], this);
          } else {
            return this.set[i];
          }
        }
      }, {
        key: 'first',
        value: function first() {
          var wrap = arguments.length > 0 && arguments[0] !== undefined ? arguments[0] : true;

          return this.ith(0, wrap);
        }
      }, {
        key: 'reversed',
        value: function reversed() {
          var set;
          set = this.set.slice();
          set.reverse();
          return new ToolkitSelection(set, this);
        }
      }, {
        key: 'reduce',
        value: function reduce(reducer) {
          var set;
          switch (typeof reducer === 'undefined' ? 'undefined' : _typeof(reducer)) {
            case 'string':
              set = this.compr(function (el) {
                if (el.is(reducer)) {
                  return el;
                }
              });
              break;
            case 'function':
              set = this.compr(reducer);
              break;
            default:
              throw 'Illegal reducer';
          }
          return new ToolkitSelection(set, this);
        }
      }, {
        key: 'extend',
        value: function extend(extension) {
          var set;
          if (extension instanceof ToolkitSelection) {
            set = extension.set;
          } else if (extension instanceof Array || extension instanceof NodeList) {
            set = ToolkitSelection.clean(extension);
          } else {
            throw 'Illegal extension';
          }
          return new ToolkitSelection(this.set.concat(set, this));
        }
      }, {
        key: 'parents',
        value: function parents() {
          var condition = arguments.length > 0 && arguments[0] !== undefined ? arguments[0] : '*';
          var high = arguments.length > 1 && arguments[1] !== undefined ? arguments[1] : true;

          var checkElement, conditionType, set;
          conditionType = ['string', 'function'].indexOf(typeof condition === 'undefined' ? 'undefined' : _typeof(condition));
          if (conditionType < 0) {
            throw 'Illegal condition';
          }
          checkElement = function checkElement(element, index) {
            if (conditionType === 0) {
              return e.is(condition);
            } else {
              return condition(element, index);
            }
          };
          set = [];
          this.iter(function (el, i) {
            var parent;
            parent = el.parentNode;
            while (parent !== ToolkitSelection.tk.config.root) {
              if (checkElement(parent, i)) {
                set.push(parent);
              }
              if (!high) {
                return;
              }
              parent = parent.parentNode;
            }
          });
          return new ToolkitSelection(set, this);
        }
      }, {
        key: 'children',
        value: function children() {
          var condition = arguments.length > 0 && arguments[0] !== undefined ? arguments[0] : '*';
          var deep = arguments.length > 1 && arguments[1] !== undefined ? arguments[1] : true;

          var conditionType, fullSet;
          conditionType = ['string', 'function'].indexOf(typeof condition === 'undefined' ? 'undefined' : _typeof(condition));
          if (conditionType < 0) {
            throw 'Illegal condition';
          }
          fullSet = [];
          this.iter(function (el, i) {
            var check, child, j, k, len, len1, ref, set, wrapped;
            el = el.first(false);
            if (el.nodeType === Node.TEXT_NODE) {
              return;
            }
            set = [];
            if (conditionType === 0) {
              if (deep) {
                set = el.querySelectorAll(condition);
              } else {
                ref = el.children;
                for (j = 0, len = ref.length; j < len; j++) {
                  child = ref[j];
                  if (child.matches(condition)) {
                    set = child;
                  }
                }
              }
            } else {
              check = deep ? el.querySelectorAll('*') : el.children;
              wrapped = new ToolkitSelection(check);
              for (k = 0, len1 = check.length; k < len1; k++) {
                child = check[k];
                if (condition(wrap, i)) {
                  set = child;
                }
              }
            }
            return fullSet = fullSet.concat(set);
          });
          return new ToolkitSelection(fullSet, this);
        }
      }, {
        key: 'copy',
        value: function copy() {
          var copy;
          copy = this.set[0].cloneNode(true);
          return new ToolkitSelection(copy, this);
        }

        //	---- Iteration and comprehension ----

      }, {
        key: 'iter',
        value: function iter(callback) {
          var el, i, j, len, ref;
          ref = this.set;
          for (i = j = 0, len = ref.length; j < len; i = ++j) {
            el = ref[i];
            el = new ToolkitSelection(el);
            if (callback(el, i) === false) {
              break;
            }
          }
          return this;
        }
      }, {
        key: 'compr',
        value: function compr(callback) {
          var el, i, j, len, ref, result, value;
          result = [];
          ref = this.set;
          for (i = j = 0, len = ref.length; j < len; i = ++j) {
            el = ref[i];
            el = new ToolkitSelection(el);
            value = callback(el, i);
            if (value !== void 0) {
              result.push(value);
            }
          }
          return result;
        }
      }, {
        key: 'is',
        value: function is(check) {
          var checkType, el, i, j, len, ref;
          checkType = ['string', 'function'].indexOf(typeof check === 'undefined' ? 'undefined' : _typeof(check));
          ref = this.set;
          for (i = j = 0, len = ref.length; j < len; i = ++j) {
            el = ref[i];
            if (checkType === 0 && (el.nodeType === Node.TEXT_NODE || !el.matches(check))) {
              return false;
            } else if (checkType === 1 && !check(new ToolkitSelection(el), i)) {
              return false;
            }
          }
          return true;
        }
      }, {
        key: 'classes',
        value: function classes() {
          var all, cls, el, i, j, k, len, len1, mine, ref;
          all = [];
          ref = this.set;
          for (i = j = 0, len = ref.length; j < len; i = ++j) {
            el = ref[i];
            mine = el.className.split(/\s+/);
            for (k = 0, len1 = mine.length; k < len1; k++) {
              cls = mine[k];
              if (indexOf.call(all, cls) < 0) {
                all.push(cls);
              }
            }
          }
          return all;
        }
      }, {
        key: 'value',
        value: function value() {
          var _value = arguments.length > 0 && arguments[0] !== undefined ? arguments[0] : _sentinel;

          if (_value === _sentinel) {
            //	Get.
            if (this.set[0].type === 'checkbox') {
              return this.set[0].checked;
            }
            _value = this.set[0].value;
            if (!_value) {
              return null;
            } else if (this.set[0].type === 'number') {
              return +_value;
            } else {
              return _value;
            }
          } else {
            //	Set.
            this.iter(function (el) {
              if (el.tag().toLowerCase() === 'select') {
                return el.children('option').attr('selected', function (gl) {
                  if (gl.attr('value' === _value)) {
                    return true;
                  } else {
                    return null;
                  }
                });
              } else {
                return el.first(false).value = _value;
              }
            });
          }
          return this;
        }
      }, {
        key: 'attr',
        value: function attr(nameOrMap) {
          var value = arguments.length > 1 && arguments[1] !== undefined ? arguments[1] : _sentinel;

          var el, j, len, ref;
          if (typeof nameOrMap === 'string') {
            if (value === _sentinel) {
              //	Get.
              return this.set[0].getAttribute(nameOrMap);
            } else {
              ref = this.set;
              //	Set.
              for (j = 0, len = ref.length; j < len; j++) {
                el = ref[j];
                if (value === null) {
                  el.removeAttribute(nameOrMap);
                } else {
                  el.setAttribute(nameOrMap, value);
                }
              }
              return this;
            }
          } else if ((typeof nameOrMap === 'undefined' ? 'undefined' : _typeof(nameOrMap)) === 'object') {
            this.iter(function (el) {
              var key;
              for (key in nameOrMap) {
                value = nameOrMap[key];
                el.attr(key, value);
              }
            });
            return this;
          } else {
            throw 'Illegal argument';
          }
        }
      }, {
        key: 'css',
        value: function css(propertyOrMap) {
          var _this2 = this;

          var value = arguments.length > 1 && arguments[1] !== undefined ? arguments[1] : _sentinel;

          var applyOne, name;
          applyOne = function applyOne(name, value) {
            name = name.replace(/-([a-z])/g, function (g) {
              return g[1].toUpperCase();
            });
            return _this2.iter(function (el, i) {
              var resolved;
              resolved = ToolkitSelection.tk.resolve(value, el, i);
              if (typeof resolved === 'number') {
                resolved += 'px';
              }
              return el.set[0].style[name] = resolved;
            });
          };
          if (typeof propertyOrMap === 'string') {
            if (value === _sentinel) {
              //	Get.
              return window.getComputedStyle(this.set[0]).getPropertyValue(propertyOrMap);
            } else {
              applyOne(propertyOrMap, value);
            }
          } else if ((typeof propertyOrMap === 'undefined' ? 'undefined' : _typeof(propertyOrMap)) === 'object') {
            for (name in propertyOrMap) {
              value = propertyOrMap[name];
              applyOne(name, value);
            }
          } else {
            throw 'Illegal argument';
          }
          return this;
        }
      }, {
        key: 'on',
        value: function on(nameOrMap) {
          var _this3 = this;

          var callback = arguments.length > 1 && arguments[1] !== undefined ? arguments[1] : _sentinel;

          var attachOne, j, len, name, ref, repr, value;
          attachOne = function attachOne(name, _callback) {
            return _this3.iter(function (el, i) {
              var pure, repr;
              pure = el.first(false);
              if (!pure.__listeners__) {
                pure.__listeners__ = [];
              }
              if (typeof name === 'function') {
                name = name(el, i);
              }
              repr = {
                event: name,
                callback: function callback(g) {
                  return _callback(el, g, i);
                }
              };
              pure.__listeners__.push(repr);
              return pure.addEventListener(repr.event, repr.callback);
            });
          };
          if (typeof nameOrMap === 'string') {
            if (callback === _sentinel) {
              //	Get.
              if (pure.__listeners__ != null) {
                ref = pure.__listeners__;
                for (j = 0, len = ref.length; j < len; j++) {
                  repr = ref[j];
                  return repr.callback;
                }
              } else {
                return [];
              }
            } else {
              attachOne(nameOrMap, callback);
            }
          } else if ((typeof nameOrMap === 'undefined' ? 'undefined' : _typeof(nameOrMap)) === 'object') {
            for (name in nameOrMap) {
              value = nameOrMap[name];
              attachOne(name, value);
            }
          } else {
            throw 'Illegal argument';
          }
          return this;
        }
      }, {
        key: 'off',
        value: function off(name) {
          var el, j, k, len, len1, list, ref, repr;
          ref = this.set;
          for (j = 0, len = ref.length; j < len; j++) {
            el = ref[j];
            list = el.__listeners__ != null || [];
            for (k = 0, len1 = list.length; k < len1; k++) {
              repr = list[k];
              if (repr.event === name) {
                el.removeEventListener(repr.event, repr.callback);
              }
            }
            el.__listeners__ = function () {
              var l, len2, results;
              results = [];
              for (l = 0, len2 = list.length; l < len2; l++) {
                repr = list[l];
                if (repr.event !== name) {
                  results.push(repr);
                }
              }
              return results;
            }();
          }
          return this;
        }
      }, {
        key: 'classify',
        value: function classify(classOrMap) {
          var _this4 = this;

          var value = arguments.length > 1 && arguments[1] !== undefined ? arguments[1] : true;
          var time = arguments.length > 2 && arguments[2] !== undefined ? arguments[2] : _sentinel;

          var _classifyOne, flag, name;
          _classifyOne = function classifyOne(name, flag, time) {
            if (flag === 'toggle') {
              //	Special second parameter case.
              flag = function flag(el, i) {
                return !e.is(selector);
              };
            }
            return _this4.iter(function (el, i) {
              var classes, flagValue, has, index, timeValue;
              flagValue = flag;
              if (typeof flagValue === 'function') {
                flagValue = flagValue(el, i);
              }
              classes = el.classes();
              has = indexOf.call(classes, name) >= 0;
              if (flagValue && !has) {
                classes.push(name);
              } else if (!flagValue && has) {
                index = classes.indexOf(name);
                classes.splice(index, 1);
              }
              el.set[0].className = classes.join(' ').trim();
              if (time !== _sentinel) {
                timeValue = time;
                if (typeof timeValue === 'function') {
                  timeValue = timeValue(el, i);
                }
                return ToolkitSelection.tk.timeout(timeValue, function (el) {
                  return _classifyOne(name, !flagValue, _sentinel);
                });
              }
            });
          };
          if (typeof classOrMap === 'string') {
            _classifyOne(classOrMap, value, time);
          } else {
            for (name in classOrMap) {
              flag = classOrMap[name];
              _classifyOne(name, flag, _sentinel);
            }
          }
          return this;
        }
      }, {
        key: 'remove',
        value: function remove() {
          var el, j, len, ref;
          ref = this.set;
          for (j = 0, len = ref.length; j < len; j++) {
            el = ref[j];
            if (el.parentNode !== null) {
              el.parentNode.removeChild(el);
            }
          }
          return this;
        }
      }, {
        key: 'append',
        value: function append(children) {
          var child, inspected, j, len, ref;
          children = new ToolkitSelection(children, this);
          children.remove();
          inspected = children.extend(children.children());
          ToolkitSelection.tk.guts.inspect(inspected);
          ref = children.set;
          for (j = 0, len = ref.length; j < len; j++) {
            child = ref[j];
            this.set[0].appendChild(child);
          }
          return children;
        }
      }, {
        key: 'prepend',
        value: function prepend(children) {
          var child, inspected, j, ref;
          children = new ToolkitSelection(children, this);
          children.remove();
          inspected = children.extend(children.children());
          ToolkitSelection.tk.guts.inspect(inspected);
          ref = children.set;
          for (j = ref.length - 1; j >= 0; j += -1) {
            child = ref[j];
            this.set[0].prepend(child);
          }
          return children;
        }
      }, {
        key: 'replace',
        value: function replace(newNode) {
          if (newNode instanceof ToolkitSelection) {
            newNode = newNode.first(false);
          }
          this.set[0].parentNode.replaceChild(newNode, this.set[0]);
          return new ToolkitSelection(newNode, this.parent);
        }
      }, {
        key: 'tag',
        value: function tag() {
          return this.set[0].tagName;
        }
      }, {
        key: 'next',
        value: function next() {
          var node = arguments.length > 0 && arguments[0] !== undefined ? arguments[0] : _sentinel;

          var el, j, len, ref;
          if (node === _sentinel) {
            if (this.empty) {
              return new ToolkitSelection([]);
            }
            return new ToolkitSelection(this.set[0].nextSibling, this);
          } else {
            if (!node instanceof ToolkitSelection) {
              node = tk(node);
            }
            ref = node.set;
            for (j = 0, len = ref.length; j < len; j++) {
              el = ref[j];
              this.set[0].parentNode.insertBefore(el, this.set[0].nextSibling);
            }
            node.parent = this;
            return node;
          }
        }
      }, {
        key: 'prev',
        value: function prev() {
          var node = arguments.length > 0 && arguments[0] !== undefined ? arguments[0] : _sentinel;

          var el, j, ref;
          if (node === _sentinel) {
            if (this.empty) {
              return new ToolkitSelection([]);
            }
            return new ToolkitSelection(this.set[0].prevSibling, this);
          } else {
            if (!node instanceof ToolkitSelection) {
              node = tk(node);
            }
            ref = node.set;
            for (j = ref.length - 1; j >= 0; j += -1) {
              el = ref[j];
              this.set[0].parentNode.insertBefore(el, this.set[0]);
            }
            node.parent = this;
            return node;
          }
        }
      }, {
        key: 'html',
        value: function html() {
          var value = arguments.length > 0 && arguments[0] !== undefined ? arguments[0] : _sentinel;

          if (value === _sentinel) {
            //	Get.
            return this.set[0].innerHTML;
          } else {
            this.iter(function (el, i) {
              return el.set[0].innerHTML = ToolkitSelection.tk.resolve(value, el, i);
            });
          }
          return this;
        }
      }, {
        key: 'text',
        value: function text() {
          var value = arguments.length > 0 && arguments[0] !== undefined ? arguments[0] : _sentinel;

          if (value === _sentinel) {
            //	Get.
            return this.set[0].textContent;
          } else {
            this.iter(function (el, i) {
              return el.set[0].textContent = ToolkitSelection.tk.resolve(value, el, i);
            });
          }
          return this;
        }
      }, {
        key: 'select',
        value: function select() {
          this.set[0].select();
          return this;
        }
      }, {
        key: 'offset',
        value: function offset() {
          var toParent = arguments.length > 0 && arguments[0] !== undefined ? arguments[0] : false;

          var el, o;
          o = {
            x: 0,
            y: 0
          };
          el = this.set[0];
          while (el) {
            o.x += el.offsetLeft;
            o.y += el.offsetRight;
            if (toParent) {
              break;
            }
            el = el.offsetParent;
          }
          return o;
        }
      }, {
        key: 'size',
        value: function size() {
          var includeInner = arguments.length > 0 && arguments[0] !== undefined ? arguments[0] : false;

          var box, el, size, style;
          el = this.set[0];
          box = el.getBoundingClientRect();
          size = {
            width: box.width,
            height: box.height
          };
          if (includeInner) {
            style = window.getComputedStyle(el, null);
            size.width += style.getPropertyValue('margin-left');
            size.width += style.getPropertyValue('margin-right');
            size.height += style.getPropertyValue('margin-top');
            size.height += style.getPropertyValue('margin-bottom');
            if ('border-box' === style.getPropertyValue('box-sizing')) {
              size.width += style.getPropertyValue('padding-left');
              size.width += style.getPropertyValue('padding-right');
              size.height += style.getPropertyValue('padding-top');
              size.height += style.getPropertyValue('padding-bottom');
            }
          }
          return size;
        }
      }]);

      return ToolkitSelection;
    }();

    ;

    ToolkitSelection.tk = null;

    return ToolkitSelection;
  }.call(this);

  guts.attach(_SelectionModule = function _SelectionModule(tk) {
    _classCallCheck(this, _SelectionModule);

    tk.ToolkitSelection = ToolkitSelection;
    ToolkitSelection.tk = tk;
  });

  ToolkitPListener = function () {
    function ToolkitPListener(object, property1) {
      _classCallCheck(this, ToolkitPListener);

      var descriptor;
      this.object = object;
      this.property = property1;
      //	Ensure tracking and property existance.
      if (!this.object.__listeners__) {
        this.object.__listeners__ = {};
      }
      if (!this.object.__listeners__[this.property]) {
        this.object.__listeners__[this.property] = [];
        descriptor = this._descriptor(this.object[this.property], this.object.__listeners__[this.property]);
        Object.defineProperty(this.object, this.property, descriptor);
      }

      //	Add this listener.
      this.object.__listeners__[this.property].push(this);
      this._changed = function () {};
      this._accessed = function () {};
    }

    _createClass(ToolkitPListener, [{
      key: '_descriptor',
      value: function _descriptor(initialValue, listeners) {
        var value;
        value = initialValue;
        return {
          get: function get() {
            var j, len, listener;
            for (j = 0, len = listeners.length; j < len; j++) {
              listener = listeners[j];
              listener._accessed(value);
            }
            return value;
          },
          set: function set(newValue) {
            var j, len, listener;
            if (value === newValue) {
              return value;
            }
            value = newValue;
            for (j = 0, len = listeners.length; j < len; j++) {
              listener = listeners[j];
              listener._changed(newValue);
            }
            return value;
          }
        };
      }
    }, {
      key: 'changed',
      value: function changed(callback) {
        var initial = arguments.length > 1 && arguments[1] !== undefined ? arguments[1] : true;

        this._changed = callback;
        if (initial) {
          //	Fire.
          callback(this.object[this.property]);
        }
        return this;
      }
    }, {
      key: 'accessed',
      value: function accessed(callback) {
        this._accessed = callback;
        return this;
      }
    }, {
      key: 'remove',
      value: function remove() {
        var index;
        index = this.object.__listeners__[this.property].indexOf(this);
        this.object.__listeners__[this.property].splice(index, 1);
        return this;
      }
    }]);

    return ToolkitPListener;
  }();

  ToolkitAListener = function () {
    function ToolkitAListener(array1) {
      _classCallCheck(this, ToolkitAListener);

      this.array = array1;
      //	Ensure tracking.
      if (!this.array.__listeners__) {
        this._mixinListeners();
      }
      this.array.__listeners__.push(this);
      this._added = function () {};
      this._removed = function () {};
      this._accessed = function () {};
    }

    _createClass(ToolkitAListener, [{
      key: '_mixinListeners',
      value: function _mixinListeners() {
        var _this5 = this;

        var innerPop, innerPush, innerSplice, listeners, updateIndicies;
        listeners = this.array.__listeners__ = [];
        updateIndicies = function updateIndicies() {
          var descriptor, i, j, ref, results;
          results = [];
          for (i = j = 0, ref = _this5.array.length; 0 <= ref ? j < ref : j > ref; i = 0 <= ref ? ++j : --j) {
            descriptor = _this5._indexDescriptor(_this5.array[i], i, listeners);
            results.push(Object.defineProperty(_this5.array, i + '', descriptor));
          }
          return results;
        };
        innerPush = this.array.push;
        this.array.push = function () {
          for (var _len2 = arguments.length, items = Array(_len2), _key2 = 0; _key2 < _len2; _key2++) {
            items[_key2] = arguments[_key2];
          }

          var i, item, j, k, len, len1, listener, start;
          start = _this5.array.length;
          innerPush.apply(_this5.array, items);
          updateIndicies();
          for (i = j = 0, len = items.length; j < len; i = ++j) {
            item = items[i];
            for (k = 0, len1 = listeners.length; k < len1; k++) {
              listener = listeners[k];
              listener._added(item, start + i);
            }
          }
          return _this5.array.length;
        };
        innerPop = this.array.pop;
        this.array.pop = function () {
          var index, j, len, listener, removed;
          removed = _this5.array[index = _this5.array.length - 1];
          innerPop.apply(_this5.array);
          updateIndicies();
          for (j = 0, len = listeners.length; j < len; j++) {
            listener = listeners[j];
            listener._removed(removed, index);
          }
          return removed;
        };
        innerSplice = this.array.splice;
        return this.array.splice = function (start, count) {
          for (var _len3 = arguments.length, items = Array(_len3 > 2 ? _len3 - 2 : 0), _key3 = 2; _key3 < _len3; _key3++) {
            items[_key3 - 2] = arguments[_key3];
          }

          var i, j, k, l, len, len1, listener, m, ref, ref1, removed, result;
          removed = function () {
            var j, ref, ref1, results;
            results = [];
            for (i = j = ref = start, ref1 = start + count; ref <= ref1 ? j < ref1 : j > ref1; i = ref <= ref1 ? ++j : --j) {
              results.push(this.array[i]);
            }
            return results;
          }.call(_this5);
          result = innerSplice.apply(_this5.array, [start, count].concat(items));
          updateIndicies();
          for (i = j = 0, ref = count; 0 <= ref ? j < ref : j > ref; i = 0 <= ref ? ++j : --j) {
            for (k = 0, len = listeners.length; k < len; k++) {
              listener = listeners[k];
              listener._removed(removed[i], start + i);
            }
          }
          for (i = l = 0, ref1 = items.length; 0 <= ref1 ? l < ref1 : l > ref1; i = 0 <= ref1 ? ++l : --l) {
            for (m = 0, len1 = listeners.length; m < len1; m++) {
              listener = listeners[m];
              listener._added(_this5.array[start + i], i);
            }
          }
          return result;
        };
      }
    }, {
      key: '_indexDescriptor',
      value: function _indexDescriptor(initialValue, index, listeners) {
        var value;
        value = initialValue;
        return {
          get: function get() {
            var listener;
            (function () {
              var j, len, results;
              results = [];
              for (j = 0, len = listeners.length; j < len; j++) {
                listener = listeners[j];
                results.push(listener._accessed(value));
              }
              return results;
            })();
            return value;
          },
          set: function set(newValue) {
            var j, k, len, len1, listener;
            if (value === newValue) {
              return value;
            }
            value = newValue;
            for (j = 0, len = listeners.length; j < len; j++) {
              listener = listeners[j];
              listener._removed(value, index);
            }
            for (k = 0, len1 = listeners.length; k < len1; k++) {
              listener = listeners[k];
              listener._added(newValue, index);
            }
            return value;
          },
          configurable: true
        };
      }
    }, {
      key: 'added',
      value: function added(callback) {
        var index, item, j, len, ref;
        this._added = callback;
        ref = this.array;
        for (index = j = 0, len = ref.length; j < len; index = ++j) {
          item = ref[index];
          callback(item, index);
        }
        return this;
      }
    }, {
      key: 'removed',
      value: function removed(callback) {
        this._removed = callback;
        return this;
      }
    }, {
      key: 'accessed',
      value: function accessed(callback) {
        this._accessed = callback;
        return this;
      }
    }]);

    return ToolkitAListener;
  }();

  guts.attach(callable(_Listeners = function () {
    function _Listeners() {
      _classCallCheck(this, _Listeners);

      this.called = 'listener';
    }

    _createClass(_Listeners, [{
      key: '_call',
      value: function _call(objectOrArray) {
        var property = arguments.length > 1 && arguments[1] !== undefined ? arguments[1] : _sentinel;

        if (objectOrArray instanceof Array) {
          return new ToolkitAListener(objectOrArray);
        } else if ((typeof objectOrArray === 'undefined' ? 'undefined' : _typeof(objectOrArray)) === 'object') {
          return new ToolkitPListener(objectOrArray, property);
        }
        throw 'Invalid parameter';
      }
    }]);

    return _Listeners;
  }()));

  ToolkitTemplate = function () {
    function ToolkitTemplate(tk1, definition1) {
      _classCallCheck(this, ToolkitTemplate);

      this.tk = tk1;
      this.definition = definition1;
      this._data = null;
    }

    _createClass(ToolkitTemplate, [{
      key: 'data',
      value: function data(_data2) {
        this._data = _data2;
        return this;
      }

      //	Realize a virtual node (as a DOM node).

    }, {
      key: '_realize',
      value: function _realize(virtual) {
        var child, item, j, len, ref, result;
        if (!virtual) {
          return document.createTextNode('');
        }
        if (typeof virtual === 'string') {
          result = document.createTextNode(virtual);
        } else if (typeof virtual === 'function') {
          result = this._realize(virtual());
        } else if (virtual instanceof Array) {
          result = function () {
            var j, len, results;
            results = [];
            for (j = 0, len = virtual.length; j < len; j++) {
              item = virtual[j];
              results.push(this._realize(item));
            }
            return results;
          }.call(this);
        } else {
          result = this.tk.tag(virtual.tag).attr(virtual.attributes);
          ref = virtual.children;
          for (j = 0, len = ref.length; j < len; j++) {
            child = ref[j];
            result.append(this._realize(child));
          }
        }
        return result;
      }
    }, {
      key: 'render',
      value: function render() {
        return this.tk(this._realize(this.definition(this._data)));
      }
    }]);

    return ToolkitTemplate;
  }();

  guts.attach(callable(_Templates = function () {
    function _Templates() {
      _classCallCheck(this, _Templates);

      this.called = 'template';
    }

    _createClass(_Templates, [{
      key: '_call',
      value: function _call(definition) {
        return new ToolkitTemplate(this, definition);
      }
    }, {
      key: 'tag',
      value: function tag(_tag, attributes) {
        for (var _len4 = arguments.length, children = Array(_len4 > 2 ? _len4 - 2 : 0), _key4 = 2; _key4 < _len4; _key4++) {
          children[_key4 - 2] = arguments[_key4];
        }

        return {
          tag: _tag,
          attributes: attributes || {},
          children: children
        };
      }
    }]);

    return _Templates;
  }()));

  Toolkit = callable(_Toolkit = function () {
    function _Toolkit() {
      var _this6 = this;

      _classCallCheck(this, _Toolkit);

      //	Define the 'here' debug helper.
      Object.defineProperty(this, 'here', {
        get: function get() {
          return _this6.log('here');
        }
      });
    }

    _createClass(_Toolkit, [{
      key: '_call',
      value: function _call(selection) {
        return new ToolkitSelection(selection);
      }
    }, {
      key: '_finalize',
      value: function _finalize(config) {
        var _this7 = this;

        var ref, ref1;
        //	Read config.
        this.config = {
          root: (ref = config.root) != null ? ref : typeof document !== "undefined" && document !== null ? document : null,
          debug: (ref1 = config.debug) != null ? ref1 : false
        };

        //	Create guts.
        this.guts = guts.onto(this);
        //	Prepare initialization.
        if (/complete|loaded|interactive/.test(typeof document !== "undefined" && document !== null ? document.readyState : void 0)) {
          this.guts.init();
        } else if (typeof window !== "undefined" && window !== null) {
          window.addEventListener('DOMContentLoaded', function () {
            return _this7.guts.init();
          });
        }
      }

      //	Initialization callback registery.

    }, {
      key: 'init',
      value: function init(callback) {
        this.guts.initFunctions.push(callback);
        return this;
      }

      //	Element inspection registery.

    }, {
      key: 'inspection',
      value: function inspection(callback) {
        this.guts.inspectionFunctions.push(callback);
        return this;
      }

      //	Logging.

    }, {
      key: 'log',
      value: function log() {
        var ref;

        for (var _len5 = arguments.length, args = Array(_len5), _key5 = 0; _key5 < _len5; _key5++) {
          args[_key5] = arguments[_key5];
        }

        if ((ref = this.config) != null ? ref.debug : void 0) {
          console.log.apply(null, args);
        }
        return args[0];
      }

      //	Function name retrieval.

    }, {
      key: 'nameOf',
      value: function nameOf(func) {
        var ref;
        return (ref = /^function\s+([\w\$]+)\s*\(/.exec(func.toString())) != null ? ref : '<anonymous function>';
      }

      //	Resolve a potentially functional parameter.
      //	DEPRICATED

    }, {
      key: 'resolve',
      value: function resolve(thing) {
        if (typeof thing !== 'function') {
          return thing;
        } else {
          for (var _len6 = arguments.length, args = Array(_len6 > 1 ? _len6 - 1 : 0), _key6 = 1; _key6 < _len6; _key6++) {
            args[_key6 - 1] = arguments[_key6];
          }

          return thing.apply(null, args);
        }
      }

      //	Current time in milliseconds.

    }, {
      key: 'time',
      value: function time() {
        return new Date().getTime();
      }

      //	Numerical range generation.

    }, {
      key: 'range',
      value: function range(max) {
        var realMax = arguments.length > 1 && arguments[1] !== undefined ? arguments[1] : null;

        var i, j, min, ref, ref1, results;
        //	Parse var-args.
        min = 0;
        if (realMax) {
          min = max;
          max = realMax;
        }
        results = [];
        for (i = j = ref = min, ref1 = max; ref <= ref1 ? j < ref1 : j > ref1; i = ref <= ref1 ? ++j : --j) {
          results.push(i);
        }
        return results;
      }

      //	Iteration.

    }, {
      key: 'iter',
      value: function iter(iterable, callback) {
        var i, item, j, len, name, value;
        if (iterable instanceof Array) {
          for (i = j = 0, len = iterable.length; j < len; i = ++j) {
            item = iterable[i];
            callback(item, i);
          }
        } else if ((typeof iterable === 'undefined' ? 'undefined' : _typeof(iterable)) === 'object') {
          for (name in iterable) {
            value = iterable[name];
            callback(name, value);
          }
        } else {
          throw 'Not iterable: ' + iterable;
        }
      }

      //	Comprehension.

    }, {
      key: 'compr',
      value: function compr(array, callback) {
        var i, item, j, len, result, returned;
        result = [];
        for (i = j = 0, len = array.length; j < len; i = ++j) {
          item = array[i];
          returned = callback(item, i);
          if (returned != null) {
            result.push(returned);
          }
        }
        return returned;
      }
    }, {
      key: 'timeout',
      value: function timeout(time, callback) {
        return setTimeout(callback, time);
      }
    }, {
      key: 'tag',
      value: function tag(tagName) {
        var attributes = arguments.length > 1 && arguments[1] !== undefined ? arguments[1] : {};

        var child, el, j, key, len, value;
        el = document.createElement(tagName);
        for (key in attributes) {
          value = attributes[key];
          el.setAttribute(key, value);
        }

        for (var _len7 = arguments.length, children = Array(_len7 > 2 ? _len7 - 2 : 0), _key7 = 2; _key7 < _len7; _key7++) {
          children[_key7 - 2] = arguments[_key7];
        }

        for (j = 0, len = children.length; j < len; j++) {
          child = children[j];
          el.appendChild(this.tag(child));
        }
        return new ToolkitSelection(el);
      }
    }]);

    return _Toolkit;
  }());

  //	Export either to the window or as a module, depending on context.
  toolkit = {
    create: function create() {
      var config = arguments.length > 0 && arguments[0] !== undefined ? arguments[0] : {};

      var tk;
      tk = new Toolkit();
      tk._finalize(config);
      return tk;
    }
  };

  if (typeof window !== "undefined" && window !== null) {
    window.toolkit = toolkit;
  } else {
    module.exports = toolkit;
  }
}).call(undefined);