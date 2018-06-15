class View {
	getRenderContext() {
		return [this.data, this.state]
	}

	render() {
		VirtualDOMRenderer.instance.render(this);
	}
}

@coreComponent
class ViewProvider {
	constructor(core) {
		this.core = core;
		core.View = View;
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
					Object.defineProperty(this, 'data', (initialValue => {
						let value = initialValue;
						return {
							set: newValue => {
								value = newValue;
								this.render();
							},
							get: () => value
						};
					})(this.data || options.data));

					this.state = this.state || options.state;
					this.template = this.template || options.template;
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