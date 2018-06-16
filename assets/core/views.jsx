class View {
	getRenderContext() {
		return [this.data, this.state]
	}

	render() {
		VirtualDOMRenderer.instance.render(this);
	}

	hasChanged(other) {
		return true;
	}
}

class PagePart {
	constructor(selector) {
		this.selector = selector;
		this.element = null;
		this.renderQueue = [];

		if (document.readyState == 'ready') {
			this.actualize();
		}
		else {
			document.addEventListener('DOMContentLoaded', this.actualize.bind(this));
		}
	}

	actualize() {
		this.element = document.querySelector(this.selector);
		for (var i = 0; i < this.renderQueue.length; i++) {
			let el = VirtualDOMRenderer.instance.render(this.renderQueue[i]);
			this.element.appendChild(el);
		}
	}

	render(renderable) {
		if (this.element) {
			this.element.appendChild(
				VirtualDOMRenderer.instance.render(renderable)
			);
		}
		else {
			this.renderQueue.push(renderable);
		}
	}
}

@coreComponent
class ViewProvider {
	constructor(core) {
		this.core = core;
		core.View = View;

		core.header = new PagePart('header.header');
		core.page = new PagePart('div.page');
		core.footer = new PagePart('footer.footer');
	}

	@exposedMethod
	observeState(view) {
		const callback = () => { this.core.render(view); }
		const observeProperty = (object, property) => {
			Object.defineProperty(object, property, (initialValue => {
				let value = initialValue;
				return {
					set: newValue => {
						value = newValue;
						callback();
					},
					get: () => value
				};
			})(object[property]));
		};
		const observeOne = item => {
			if (typeof item != 'object') return;

			if (item instanceof Array) {
				//	TODO: Watch array.
			}
			else {
				let propertyNames = Object.getOwnPropertyNames(item);
				for (let i = 0; i < propertyNames.length; i++) {
					observeProperty(item, propertyNames[i]);
				}
			}
		}

		observeOne(view.state);
	}

	@exposedMethod
	view(options) {
		return (ViewClass) => {
			class DerivedViewClass extends ViewClass {
				constructor(...args) {
					super(...args);
					this.element = this.referenceDOM = null;
					this.state = this.state || options.state;
					this.template = this.template || options.template;

					const self = this;
					Object.defineProperty(this, 'data', (initialValue => {
						let value = null;
						const set = newValue => {
							if (newValue instanceof DataCache) {
								newValue.addView(self);
								value = newValue.data;
							}
							else {
								value = newValue;
							}
							self.render();
						}
						set(initialValue);
						return {
							set: set,
							get: () => value
						};
					})(this.data || options.data));
				}
			}

			let Current = DerivedViewClass.prototype;
			while (Object.getPrototypeOf(Current) !== Object.prototype) {
				Current = Object.getPrototypeOf(Current);
				if (Current === View.prototype) return;
			}
			
			Object.setPrototypeOf(Current, View.prototype);
			
			return DerivedViewClass;
		}
	}
}