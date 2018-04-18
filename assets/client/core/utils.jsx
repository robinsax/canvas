@part
class CoreUtilsPart {
	constructor() {
		core.utils = this;

		core.onSetup = this.createMethodDecorator('_onSetup');
	}

	nameToTitle(n) {
		return n.replace(/(_|^)(\w)/g, (m, s, l) => (' ' + l.toUpperCase()));
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

	invokeDecoratedMethods(instance, cls, annotation, ...args) {
		this.iterateMethodDecorated(cls, annotation, key => instance[key](...args));
	}

	installObjectObservers(object, callback) {
		if (!object || object._watched) { return; }
		object._watched = true;

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