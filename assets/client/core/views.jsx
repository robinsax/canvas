@part
class ViewPart {
	constructor() {
		this._viewDefinitions = {};

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
			el.reduce(eventDesc.selector).on(eventDesc.on, (tel, event) => {
				instance[eventDesc.key](tel, event);
			});
		});
		core.utils.iterateDecoratedMethods(cls, '_inspectors', desc => {
			el.reduce(desc.selector).iter(tel => { instance[desc.key](tel); });
		});
	}

	view(options) {
		return (ViewClass) => {
			let name = ViewClass.name.toLowerCase();

			class View extends ViewClass {
				constructor() {
					super(...arguments);
					this.name = name;
					this.updateOptionDefaults = this.updateOptionDefaults || (x => x);
					core.utils.applyOptionalizedArguments(this, options, this.updateOptionDefaults({
						state: {},
						templates: null,
						template: null,
						data: {},
						dataSource: null,
						query: {}
					}));

					this.base = {
						fetch: (then=(() => {})) => {
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
						},
						select: () => this.node,
						render: () => {
							if (this._rendering){ return; }
							this._rendering = true;

							let boundRender = () => this.render();

							if (!this._created) {
								this._created = true;
								tk.listener(this, 'data').changed(() => this.render());
							}
							core.utils.installObjectObservers(this.data, boundRender);
							core.utils.installObjectObservers(this.state, boundRender);

							this.node = this._templateContext
								.data(this.data, this.state, this.templates)
								.render();
							
							this._rendering = false;
							return this.node;
						}
					}

					tk.iter(this.base, (key, func) => {
						if (!this[key]) {
							this[key] = (...a) => func(...a);
						}
					});
					core.utils.invokeDecoratedMethods(this, ViewClass, '_onSetup');
					
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
						}
					});

					this.node = null;
					this._templateContext = tk.template(this.template || this.templates.root)
						.inspection(el => {
							core.utils.resolveEventsAndInspections(this, ViewClass, el);
						})
						.live();
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
					tk.log('Created view ' + viewName + ' as ' + label);
				});
			}
			
			if (view.dataSource){ view.fetch(create); }
			else { create(); }
		});
	}

	viewEvent(on, selector) {
		if (!selector) {
			selector = on;
			on = 'click';
		}

		return core.utils.createMethodDecorator('_events', key => {
			return {
				selector: selector,
				on: on,
				key: key
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
				this.isOpen = false;

				this.template = ((self) => () => 
					<div class={ "modal" + (self.className ? " " + self.className : "") + (self.isOpen ? " open" : "") }>
						<div class="panel">
							<i class="fa fa-times close"/>
							{ self.templates.panel(self.data, self.state, self.templates) }
						</div>
					</div>)(this);
			}
			
			updateOptionDefaults(options) {
				options.className = null;
				return options;
			}
		
			@core.event('.modal, .close')
			close() {
				this.isOpen = false;
				this.select().classify('open', false);
			}
		
			open() {
				this.isOpen = true;
				this.select().classify('open');
			}
		
			@core.event('.panel')
			keepOpen(el, event) {
				event.stopPropagation();
			}
		}

		class ListView {
			updateOptionDefaults(defaults) {
				defaults.className = null;
				defaults.listRoot = 'ul';
				defaults.iterated = null;
				return defaults;
			}

			@core.onSetup
			setupTemplates() {
				this.templates = this.templates || {};
				this.templates.header = this.templates.header || (() => {});
				this.templates.item = this.templates.item || (item => <li>{ typeof item == 'object' ? JSON.stringify(item) : item + '' }</li>)
				this.templates.empty = this.templates.empty || (() => <p class="subtext">No items to show</p>)
				this.templates.footer = this.templates.footer || (() => {});

				this.template = this.template || ((self) => {
					let iterTarget = () => self.iterated ? self.data[self.iterated] : self.data;
					
					return (data, state, templates) =>
						<div class={ "list-container" + (self.className ? " " + self.className : "") }>
							{ templates.header(data, state, templates) }
							{
								tk.template.tag(
									self.listRoot,
									null,
									( iterTarget().length > 0 ? 
										() => tk.comp(iterTarget(), (item, i) => templates.item(item, i, state, templates))
										:
										() => templates.empty(data, state, templates)
									)
								)
							}
							{ templates.footer(data, state, templates) }
						</div>
				})(this);
			}
		}

		core.ModalView = ModalView;
		core.ListView = ListView;
	}
}
