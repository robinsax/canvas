//	::include core.root, core.logging, core.resources, core.virtual_dom, core.views
//	::export canvas --hard

const log = new Logger('canvas');

class CanvasCore {
	constructor() {
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
}

const canvas = new CanvasCore();
log.info('canvas initialized');
