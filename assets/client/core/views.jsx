class State {
	constructor(state) {
		Object.defineProperty(this, '_', {
			value: {
				toInstall: null
			},
			enumerable: false
		});
		this.update(state);
	}

	activate(callback) {
		this._.toInstall = callback;
		core.utils.installObjectObservers(this, this._.toInstall);
	}

	update(updates) {
		tk.update(this, updates);
		if (!this._.toInstall) {
			return;
		}

		core.utils.installObjectObservers(this, this._.toInstall);
	}
}

class RootView {
	__construct(options) {
		let state = new State(this.state || {});
		state.update(options.state || {});
		Object.defineProperty(this, 'state', {
			value: state,
			writable: false
		});

		this.persistant = options.persistant || this.persistant || [];

		this.data = options.data || this.data || {};

		this.template = options.template || this.template || null;
		this.templates = this.templates || {};
		tk.update(this.templates, options.templates || {});

		if (!this.template) {
			this.template = this.templates.root;
		}

		this.dataSource = options.dataSource || this.dataSource || null;
		this.query = this.query || {};
		tk.update(this.query, options.query || {});

		Object.defineProperties(this, {
			_rendering: {
				value: false,
				writable: true,
				enumerable: false
			},
			_created: {
				value: false,
				writable: true,
				enumerable: false
			},
			_templateContext: {
				value: null,
				writable: true,
				enumerable: false
			}
		});
		
		this.node = null;

		core._loadPersistedViewState(this.__name__, this);
	}

	fetch(then=(() => {})) {
		if (!this.dataSource) {
			throw 'Cannot fetch without dataSource';
		}

		cv.request('get', this.dataSource)
			.query(this.query)
			.success(response => {
				this.data = response.data;
				then();
			})
			.send();
	}

	render() {
		if (this._rendering){ return; }
		this._rendering = true;
		
		if (!this._templateContext) {
			this._templateContext = tk.template(this.template || this.templates.root)
				.inspection(el => {
					core.utils.resolveEventsAndInspections(this, el);
				})
				.live();
		}

		let boundRender = this.render.bind(this);
		this.state._.toInstall = boundRender;

		if (!this._created) {
			this._created = true;
			tk.listener(this, 'data').changed(boundRender);
		}
		this.state.activate(boundRender);

		this.node = this._templateContext
			.data(this.data, this.state, this.templates)
			.render();
		
		this._rendering = false;
		return this.node;
	}

	select() { return this.node; }
}

@part
class ViewPart {
	constructor() {
		this._viewDefinitions = {};

		core.State = State;
		core.View = RootView;
		
		core.view = this.view.bind(this);
		core.views = this.views = {};
		
		core.utils.resolveEventsAndInspections = this.resolveEventsAndInspections.bind(this);
		core.event = (on, selector=null) => this.viewEvent(on, selector);
		core.inspects = this.viewInspect.bind(this);

		core._loadPersistedViewState = this.loadPersistedViewState.bind(this);

		this.defineDefaultViews();
		tk(window).on({
			load: this.createViews.bind(this),
			beforeunload: this.persistViewStates.bind(this)
		});
	}

	resolveEventsAndInspections(instance, el) {
		core.utils.iterateAnnotated(instance, 'isEvent', (prop, desc) => {
			el.reduce(desc.selector).on(desc.on, (...args) => {
				if (desc.transform) {
					args = desc.transform.apply(null, args) || [];
				}
				instance[prop](...args);
			});
		});
		core.utils.iterateAnnotated(instance, 'isInspection', (prop, desc) => {
			el.reduce(desc.selector).iter(tel => { instance[prop](tel); });
		});
	}

	view(options) {
		return ViewClass => {
			let name = ViewClass.name.toLowerCase();

			core.utils.setRootPrototype(ViewClass, RootView);
			let View = (() => class View extends ViewClass {
				constructor(label) {
					super();
					this.__name__ = label;
					this.__construct(options);
					core.attachMixins(this, options.mixins || []);
				}
			})();
			
			this._viewDefinitions[name] = View;
			return View;
		}
	}
	
	createViews() {
		core.utils.iterateNonStandardTags((el, viewName) => {
			if (!this._viewDefinitions[viewName]) {
				return;
			}

			let label = el.attr('data-name') || el.attr('name') || viewName, 
				view = new this._viewDefinitions[viewName](label);
			this.views[label] = view;

			let create = () => {
				core.onceReady(() => {
					el.replace(view.render());
					tk.log('Created view ' + label);
				});
			}
			
			if (view.dataSource){ view.fetch(create); }
			else { create(); }
		});
	}

	loadPersistedViewState(viewName, view) {
		let persisted = core.unstore(viewName);
		if (!persisted) return;

		view.state.update(JSON.parse(persisted));
	}

	persistViewStates() {
		tk.iter(this.views, (viewName, view) => {
			let toStore = {};
			tk.iter(view.persistant, prop => {
				toStore[prop] = view.state[prop];
			});
			core.store(viewName, JSON.stringify(toStore));
		});
	}

	viewEvent(on, selector, transform=null) {
		if (typeof selector == 'function') {
			transform = selector;
			selector = on;
			on = 'click';
		}
		if (!selector) {
			selector = on;
			on = 'click';
		}

		return core.utils.createAnnotationDecorator('isEvent', key => {
			return {
				selector: selector,
				on: on,
				transform: transform
			};
		});
	}

	viewInspect(selector) {
		return core.utils.createAnnotationDecorator('isInspection', key => {
			return {
				selector: selector
			};
		})
	}

	defineDefaultViews() {
		class ListView {
			constructor() {
				this.state = {
					className: null,
					listRoot: <ul/>,
					iteratedKey: null
				};

				this.templates = {
					header: () => {},
					item: item => <li>{ typeof item == 'object' ? JSON.stringify(item) : item + '' }</li>,
					empty: () => <p class="subtext">No items to show</p>,
					footer: () => {}
				};

				let getIterTarget = () => this.state.iteratedKey ? this.data[this.state.iteratedKey] : this.data;
				this.template = (data, state, templates) =>
					<div class={ "list-container" + (state.className ? " " + state.className : "") }>
						{ templates.header(data, state, templates) }
						{
							tk.template.tag(
								state.listRoot.tag,
								{class: 'list'},
								( getIterTarget().length > 0 ? 
									() => tk.comp(getIterTarget(), (item, i) => templates.item(item, i, state, templates))
									:
									() => templates.empty(data, state, templates)
								)
							)
						}
						{ templates.footer(data, state, templates) }
					</div>
			}
		}

		core.ListView = ListView;
	}
}
