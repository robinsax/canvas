@part
class CoreUtilsPart {
	constructor() {
		core.utils = this;

		core.onSetup = this.createMethodDecorator('_onSetup');
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

	applyOptionalizedArguments(instance, options, defaults) {
		tk.iter(defaults, (key, defaultValue) => {
			if (instance[key]) { return; }
			instance[key] = (options[key] || defaultValue);
		});
	}

	createMethodDecorator(annotation, transform=x => x) {
		return (target, key) => {
			if (!target[annotation]) {
				Object.defineProperty(target, annotation, {
					value: [],
					enumerable: false
				});
			}
			target[annotation].push(transform(key));
		}
	}

	iterateDecoratedMethods(cls, annotation, callback) {
		tk.iter(cls.prototype[annotation] || [], key => callback(key));
	}

	invokeDecoratedMethods(instance, cls, annotation, ...args) {
		this.iterateDecoratedMethods(cls, annotation, key => instance[key](...args));
	}

	installObjectObservers(object, callback) {
		if (!object || object._watched) { return; }

		if (typeof object == 'object') {
			Object.defineProperty(object, '_watched', {
				value: true,
				enumerable: false
			});
		}
		else {
			object._watched = true;
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
					.changed(value => {
						callback();
					});
			});
		}
	}
}