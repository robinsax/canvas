@part
class CoreUtilsPart {
	constructor(core) {
		core.utils = this;
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

	iterateMethodDecorated(cls, annotation, callback) {
		tk.iter(cls.prototype[annotation] || [], key => callback(key));
	}

	invokeMethodDecoratored(instance, cls, annotation, ...args) {
		this.iterateMethodDecorated(cls, annotation, key => instance[key](...args));
	}

	installObjectObservers(object, callback) {
		if (data._watched){ return; }
		Object.defineProperty(data, '_watched', {
			value: true,
			enumerable: false
		});

		if (data instanceof Array){
			tk.listener(data)
				.added(item => {
					watch(item, callback);
					callback();
				})
				.removed(item => {
					callback();
				});
		}
		else if (typeof data == 'object' && data !== null) {
			tk.iter(data, (property, value) => {
				watch(value, callback);
				tk.listener(data, property)
					.changed((value) => {
						callback();
					});
			});
		}
	}
}