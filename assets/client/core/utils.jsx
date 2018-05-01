@part
class CoreUtilsPart {
	constructor() {
		core.utils = this;
	}

	nameToTitle(n) {
		return n.replace(/(_|^)(\w)/g, (m, s, l) => (' ' + l.toUpperCase()));
	}

	iterateNonStandardTags(callback) {
		tk('body *').iter(el => {
			let xName = /^[xX]-(\w+)$/.exec(el.tag());

			if (xName) { 
				callback(el, xName[1].toLowerCase());
			}
		});
	}

	setRootPrototype(Top, Root) {
		let last = Top.prototype;
		while (Object.getPrototypeOf(last) != Object.prototype) {
			last = Object.getPrototypeOf(last);
			if (last == Root.prototype) {
				return;
			}
		}
		
		Object.setPrototypeOf(last, Root.prototype);
	}

	putOptions(instance, options, defaults) {
		tk.iter(defaults, (key, defaultValue) => {
			if (instance[key]) { return; }
			instance[key] = (options[key] || defaultValue);
		});
	}

	createAnnotationDecorator(annotation, valueGenerator=x => true) {
		return (target, key) => {
			target[key][annotation] = valueGenerator(key);
		}
	}

	iterateAnnotated(target, annotation, callback) {
		let proto = Object.getPrototypeOf(target);
		
		while (proto != Object.prototype) {
			let props = Object.getOwnPropertyNames(proto);

			tk.iter(props, prop => {
				if (proto[prop][annotation]) {
					callback(prop, proto[prop][annotation]);
				}
			});
			
			proto = Object.getPrototypeOf(proto);
		}
	}

	invokeAnnotated(target, annotation, ...args) {
		this.iterateAnnotated(target, annotation, prop => {
			target[prop](...args);
		});
	}

	installObjectObservers(object, callback) {
		if (!object) { return; }

		if (!object._watched) {
			if (typeof object == 'object') {
				Object.defineProperty(object, '_watched', {
					value: true,
					enumerable: false
				});
			}
			else {
				object._watched = true;
			}
		}

		if (object instanceof Array){
			tk.listener(object)
				.added(item => {
					this.installObjectObservers(item, callback);
					callback();
				})
				.removed(item => {
					callback();
				});
		}
		else if (typeof object == 'object' && object !== null) {
			tk.iter(object, (property, value) => {
				this.installObjectObservers(value, callback);
				tk.listener(object, property)
					.changed(value => { callback(); });
			});
		}
	}
}