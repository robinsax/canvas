/*
*	Views are classes that render data as HTML using an associated JSX 
*	template. The default render context for a given view's template is its
*	data, state, and subtemplate map. In canvas a template does not have
*	access to the `this` of its view to encourage maintainable frontend 
*	architecture.
*/

class View {
	/* The root view class. Override is invariantly implicit. */

	onceConstructed() {}
	onceCreated() {}
	onceFetched() {}

	processState() {}

	attachToParent(parent) {
		parent.children.push(this);
	}

	getRenderContext() {
		/* Return the render context to pass to this views template. */
		let context = [];
		if (this.data) {
			context.push(this.data);
		}
		if (this.state) {
			context.push(this.state);
		}
		if (this.subtemplates) {
			context.push(this.subtemplates);
		}
		return context;
	}

	validateForm() {
		let pass = true;
		for (let name in this.fields) {
			pass = this.fields[name].validate() && pass;
		}
		return pass;
	}
	
	get formData() {
		let data = {};
		for (let name in this.fields) {
			let field = this.fields[name];
			if (field.unincluded) continue;
			
			data[name] = field.value;
		}
		return data;
	}

	fetch() {
		this.dataCache.fetch();
	}

	submitSuccess(response) {}
	submitFailure(response) {
		let data = response.data;
		if (data.errors) {
			for (let name in data.errors) {
				this.fields[name].invalidate(data.errors[name]);
			}
		}
		if (data.error_summary) {
			if (this.errorSummary) {
				this.errorSummary.show(data.error_summary)
			}
			else {
				View.log.warning('No error summary sub-view');
			}
		}
	}

	clearForm() {
		for (let key in this.fields) {
			this.fields[key].value = null;
		}

		if (this.errorSummary) {
			this.errorSummary.hide();
		}
	}

	fillForm(data) {
		this.clearForm();
		for (let key in data) {
			if (!this.fields[key]) continue;

			this.fields[key].value = data[key];
		}
	}

	submitForm(method=null, url=null, extras={}) {
		if (!this.validateForm()) return;

		//	Update extras.
		let data = this.formData;
		for (let key in extras) {
			data[key] = extras[key];
		}

		return cv.request(method || this.formMethod, url || this.formRoute, data)
			.success(this.submitSuccess.bind(this))
			.failure(this.submitFailure.bind(this));
	}

	render() {
		/* Re-render this view. */
		if (!this.created) return;
		
		VirtualDOMRenderer.instance.render(this);
	}
}

class ModalMixin {
	constructor(className) {
		this.className = className;
	}

	updateHostOptions(options) {
		options.state = options.state || {};
		options.state.open = false;
	}

	attachToHost(host) {
		const innerTemplate = host.template;
		host.template = (...args) =>
			<div class={ "modal " + this.className + (host.state.open ? " open" : "") }>
				<div class="panel">
					<i class="fa fa-times close"/>
					{ innerTemplate(...args) }
				</div>
			</div>
		
		if (!host.open) {
			host.open = (function() { this.state.open = true; }).bind(host);
		}
		if (!host.close) {
			host.close = (function() { this.state.open = false; }).bind(host);
		}
		host.__stopEvent__ = context => context.event.stopPropagation();
		host.__events__.push(
			['.close', 'click', 'close'],
			['.modal', 'click', 'close'],
			['.panel', 'click', '__stopEvent__']
		);
	}
}

class PagePart {
	/* A segment of the page to which components can be added. */

	constructor(selector) {
		this.selector = selector;
		this.element = null;
		this.renderQueue = [];

		onceReady(this.actualize.bind(this));
	}

	actualize() {
		/*
		*	Once the DOM is available, bind to the appropriate element and
		*	perform any pending renders.
		*/
		this.element = document.querySelector(this.selector);
		for (var i = 0; i < this.renderQueue.length; i++) {
			let el = VirtualDOMRenderer.instance.render(this.renderQueue[i]);
			this.element.appendChild(el);
		}
	}

	render(renderable) {
		/*
		*	Render a JSX snippet or `View` onto this part of the page.
		*/
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
	/* The view manager and API exposure. */

	constructor(core) {
		//	Expose the View type for type checks.
		View.log = new Logger('views');
		core.View = View;
		core.ModalMixin = ModalMixin;

		//	Preset component definitions require access to this instance.
		ViewProvider.instance = this;

		//	Create page parts.
		core.header = new PagePart('header.header');
		core.mainPage = new PagePart('div.page');
		core.footer = new PagePart('footer.footer');
	}

	@exposedMethod
	event(selector, on='click') {
		return (target, key, descriptor) => {
			target.__events__ = target.__events__ || [];
			target.__events__.push([selector, on, key]);
		}
	}

	@exposedMethod
	page(route, part='mainPage') {
		return (ViewClass) => {
			if (route !== true && route != '*' && route != document.head.getAttribute('data-route')) return;

			onceReady(() => {
				cv[part].render(new ViewClass());
			});
		}
	}

	@exposedMethod
	view(options) {
		/*
		*	The view class decorator used to define views. `option` should be
		*	a map containing `template`,a function that returns a JSX snippet,
		*	as well as any of the following:
		*		* `state` - A map containing the initial state of the view
		*		* `data` - The data or target data cache as returned by `fetch`
		*		* `formModel` - The model, as loaded with `::load_model`, to
		*			use as the reference for form fields within this view.
		*/
		return (ViewClass) => {
			//	Create a derived view class.
			if (options.mixins) {
				for (let i = 0; i < options.mixins.length; i++) {
					let mixin = options.mixins[i];
					mixin.updateHostOptions(options);
				}
			}
			class DerivedViewClass extends ViewClass {
				constructor(...args) {
					super(...args);

					//	Process `options`.
					this.element = this.referenceDOM = null;
					this.state = new State(options.state);
					this.template = options.template;
					this.subtemplates = options.subtemplates || null;
					this.formModel = options.formModel || null;
					this.formMethod = options.formMethod || 'post';
					this.formRoute = options.formRoute || document.head.getAttribute('data-route');

					this.created = false;
					this.children = [];
					this.parent = null;

					const self = this;
					Object.defineProperty(this, 'data', (initialValue => {
						let value;
						if (initialValue instanceof DataCache) {
							initialValue.addView(self);
							self.dataCache = initialValue;
							value = initialValue.data;
						}
						else {
							value = initialValue;
						}
						
						return {
							set: set = newValue => {
								if (newValue instanceof DataCache) {
									newValue.addView(self);
									self.dataCache = self;
									newValue = newValue.data;
								}
								value = newValue;
								self.render();	
							},
							get: () => value
						};
					})(options.data));

					this.onceConstructed(...args);
					if (options.mixins) {
						for (let i = 0; i < options.mixins.length; i++) {
							let mixin = options.mixins[i];
							mixin.attachToHost(this);
						}
					}
				}
			}

			//	Ensure this class extends the View prototype.
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