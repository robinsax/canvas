@part
class ViewPart {
	constructor() {
		this._viewDefinitions = {};

		core.view = (name, definition) => this.view(name, definition);
		core.views = this.views = {};

		core.utils.resolveEvents = (instance, cls, el) => this.resolveEvents(instance, cls, el);

		core.event = (on, selector=null) => this.viewEvent(on, selector)
		core.onCreate = core.utils.createMethodDecorator('_onCreate');
		core.onRender = core.utils.createMethodDecorator('_onRender');

		this.defineDefaultViews(core);

		tk(window).on('load', () => this.createViews());
	}

	resolveEvents(instance, cls, el) {
		core.utils.iterateMethodDecorated(cls, '_events', eventDesc => {
			if (el.is(eventDesc.selector)) {
				el.on(eventDesc.on, (tel, event) => {
					instance[eventDesc.key](tel, event);
				});	
			}
			el.children(eventDesc.selector).on(eventDesc.on, (tel, event) => {
				instance[eventDesc.key](tel, event);
			});
		});
	}

	view(name, options) {
		return (ViewClass) => {
			class View extends ViewClass {
				constructor() {
					super(...arguments);
					this.updateOptionDefaults = this.updateOptionDefaults || (x => x);
					core.utils.applyOptionalizedArguments(this, options, this.updateOptionDefaults({
						state: {},
						templates: null,
						template: null,
						data: {},
						dataSource: null
					}));
					if (!this.template && this.templates) {
						this.template = this.templates.root;
					}

					this.base = {
						fetch: (then=(() => {})) => {
							if (!this.dataSource) {
								throw 'Cannot fetch without dataSource';
							}

							cv.request('get', this.dataSource)
								.success(response => {
									this.data = response.data;
									this.render();
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
								core.utils.invokeDecoratedMethods(this, ViewClass, '_onCreate');
								this._created = true;
								tk.listener(this, 'data').changed(() => this.render());
							}
							core.utils.installObjectObservers(this.data, boundRender);
							core.utils.installObjectObservers(this.state, boundRender);

							let el = tk.template(this.template)
								.data(this.data, this.state, this.templates)
								.render();

							core.utils.resolveEvents(this, ViewClass, el);
							
							if (this.node && !this.node.parents('body').empty){
								this.node.replace(el);
							}
							this.node = el;

							core.utils.invokeDecoratedMethods(this, ViewClass, '_onRender', el);
	
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
				}
			}
			
			this._viewDefinitions[name] = View;
			return View;
		}
	}

	createViews() {
		tk('cv-view').iter(el => {
			let name = el.attr('cv-name'), 
				ViewClass = this._viewDefinitions[name];

			if (!ViewClass) {
				tk.warn('No such view: ' + name);
				return;
			}

			let label = el.attr('cv-label') || name,
				view = new ViewClass();
			this.views[label] = view;

			let create = () => {
				core.onceReady(() => {
					tk.log('Created view ' + name + (label != name ? ' (as ' + label + ')' : ''));
					el.replace(view.render());
				});
			};
			
			if (view.dataSource){
				view.fetch(create);
			}
			else {
				create();
			}
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
	
	defineDefaultViews(core) {
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
			
			template() {
				return 
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
