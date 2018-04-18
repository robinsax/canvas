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

								tk.listener(this, 'data').changed(boundRender);
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
							this[key] = () => func(...arguments);
						}
					});
					
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
				tk.warn('No Such View: ' + name);
				return;
			}

			let label = el.attr('cv-label') || name,
				view = new ViewClass();
			this.views[label] = view;

			let create = () => {
				core.onceReady(() => {
					tk.log('Created View ' + name + (label ? ' (as ' + label + ')' : ''));
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
			}
			
			updateOptionDefaults(options) {
				options.className = null;
				return options;
			}
			
			template() {
				return <div class={ "modal" + (this.className ? " " + this.className : "") + (this.isOpen ? " open" : "") }>
					<div class="panel">
						<i class="fa fa-times close"/>
						{ this.templates.panel(this.data, this.state, this.templates) }
					</div>
				</div>
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

		core.ModalView = ModalView;
	}
}
