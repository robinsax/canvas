class State {
	constructor(state) {
		this.update(state);
	}

	update(updates) {
		tk.update(this, updates);
	}
}

class RootView {
	__construct(options) {
		this.state = new State(this.state || {});
		this.state.update(options.state || {});

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
					core.utils.resolveEventsAndInspections(this, this.__cls, el);
				})
				.live();
		}

		let boundRender = () => this.render();

		if (!this._created) {
			this._created = true;
			tk.listener(this, 'data').changed(boundRender);
		}
		core.utils.installObjectObservers(this.data, boundRender);
		core.utils.installObjectObservers(this.state, boundRender);

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

		core._State = State;
		
		core.view = (name, definition) => this.view(name, definition);
		core.views = this.views = {};

		core.utils.resolveEventsAndInspections = (instance, cls, el) => this.resolveEventsAndInspections(instance, cls, el);
		core.event = (on, selector=null) => this.viewEvent(on, selector);
		core.inspects = selector => this.viewInspect(selector);

		this.defineDefaultViews();
		tk(window).on('load', () => this.createViews());
	}

	resolveEventsAndInspections(instance, cls, el) {
		core.utils.iterateDecoratedMethods(cls, '_events', eventDesc => {
			
			//	TODO: Remove once annotation storage safe
			if (!instance[eventDesc.key]) { return; }

			el.reduce(eventDesc.selector).on(eventDesc.on, (...a) => {
				if (eventDesc.transform) {
					a = eventDesc.transform.apply(null, a) || [];
				}
				instance[eventDesc.key](...a);
			});
		});
		core.utils.iterateDecoratedMethods(cls, '_inspectors', desc => {
			el.reduce(desc.selector).iter(tel => { instance[desc.key](tel); });
		});
	}

	view(options) {
		return ViewClass => {
			let name = ViewClass.name.toLowerCase();

			core.utils.setRootPrototype(ViewClass, RootView);
			class View extends ViewClass {
				constructor() {
					super();
					this.__cls = ViewClass;
					this.__construct(options);
				}
			}
			
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
				view = new this._viewDefinitions[viewName]();
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

		return core.utils.createMethodDecorator('_events', key => {
			return {
				selector: selector,
				on: on,
				key: key,
				transform: transform
			}
		});
	}

	viewInspect(selector) {
		return core.utils.createMethodDecorator('_inspectors', key => {
			return {
				selector: selector,
				key: key
			};
		})
	}

	defineDefaultViews() {
		class ModalView {
			constructor() {
				this.state = {
					isOpen: false,
					className: null
				};

				this.template = (data, state, templates) => 
					<div class={ "modal" + (state.className ? " " + state.className : "") + (state.isOpen ? " open" : "") }>
						<div class="panel">
							<i class="fa fa-times close"/>
							{ templates.panel(data, state, templates) }
						</div>
					</div>
			}

			@core.event('.modal, .close')
			close() {
				this.state.isOpen = false;
			}

			open() {
				this.state.isOpen = true;
			}

			@core.event('.panel')
			keepOpen(el, event) {
				event.stopPropagation();
			}
		}

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

		core.ModalView = ModalView;
		core.ListView = ListView;
	}
}
