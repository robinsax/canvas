//	::include core.root, core.logging, core.resources, core.virtual_dom
//	::export canvas --hard

const log = new Logger('canvas');

class CanvasCore {
	constructor() {
		for (var i = 0; i < coreComponents.length; i++) {
			let ComponentClass = coreComponents[i],
				instance = new ComponentClass(),
				methods = Object.getOwnPropertyNames(Object.getPrototypeOf(instance));

			for (var j = 0; j < methods.length; j++) {
				let methodName = methods[j], method = instance[methodName];
				if (method.isExposed) {
					this[methodName] = (...args) => method(...args);
				}
			}
		}
	}
}

const canvas = new CanvasCore();
log.info('canvas initialized');
