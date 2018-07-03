
//	::include core.root, core.shims, core.logging, core.resources, core.state, core.virtual_dom, core.views, core.requests, core.data, core.forms, core.svg
//	::export canvas --hard

const log = new Logger('canvas'); 

class CanvasCore {
	constructor() {
		this.route = document.head.getAttribute('data-route');
		this.onceReady = onceReady;
		for (var i = 0; i < coreComponents.length; i++) {
			let ComponentClass = coreComponents[i],
				instance = new ComponentClass(this),
				methods = Object.getOwnPropertyNames(Object.getPrototypeOf(instance));

			for (var j = 0; j < methods.length; j++) {
				let methodName = methods[j], method = instance[methodName];
				if (method.isExposed) {
					this[methodName] = (function(...args) { return method.apply(this, args); }).bind(instance);
				}
			}
		}
	}

	iter(iterable, callback) {
		if (iterable instanceof Array) {
			for (let i = 0; i < iterable.length; i++) {
				callback(iterable[i], i);
			}
		}
		else {
			for (let key in iterable) {
				callback(key, iterable[key]);
			}
		}
	}

	//	TODO: extend.
	aggr(iterable, callback) {
		let total = 0;
		for (let i = 0; i < iterable.length; i++) {
			total += callback(iterable[i], i);
		}
		return total;
	}

	classify(element, className, flag=true) {
		let classList = element.className.split(' '),
			k = classList.indexOf(className);
		if (k < 0 && flag) {
				element.className += ' ' + className;
		}
		if (k > 0 && !flag) {
			classList.splice(k, 1);
			element.className = classList.join(' ');
		}
	}
}

window.canvas = window.cv = new CanvasCore();
log.info('canvas initialized');
