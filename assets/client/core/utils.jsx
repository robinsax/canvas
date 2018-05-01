@part
class CoreUtilsPart {
	constructor() {
		core.utils = this;

		this.decorations = {};
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
				//	This will happen all but the first time.
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

	//	TODO: Need a safe storage for annotations (this is a super-hacky hotfix).
	createMethodDecorator(annotation, transform=x => x) {
		return (target, key) => {
			if (!target.constructor[annotation]) {
				target.constructor[annotation] = [];
			}

			target.constructor[annotation].push(transform(key));
		}
	}

	//	TODO: Use fix here.
	iterateDecoratedMethods(cls, annotation, callback) {
		tk.iter(cls[annotation] || [], key => callback(key));
	}

	invokeDecoratedMethods(instance, cls, annotation, ...args) {
		this.iterateDecoratedMethods(cls, annotation, key => { 
			// TODO: Remove this hotfix.
			if (!instance[key]) {
				return;
			}
			
			instance[key](...args)
		});
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