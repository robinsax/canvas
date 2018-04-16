@part
class ViewPart {
	static instance = null;

	constructor(core) {
		ViewPart.instance = this;
		this.core = core;

		core.views = this.views = {};
		this._viewDefinitions = {};

		core.view = (name, definition) => this.view(name, definition);

		core.event = (on, selector=null) => this.viewEvent(on, selector)
		core.onCreate = (target, key, property) => this.viewOnCreate(target, key, property);
		core.onRender = (target, key, property) => this.viewOnRender(target, key, property);

		tk(window).on('load', () => this.createViews());
	}

	view(name, definition) {
		return (ViewClass) => {
			class View extends ViewClass {
				constructor() {
					super(...arguments);
					this.state = this.state || definition.state ||  {};
					this.templates = this.templates || definition.templates || null;
					this.template = this.template || definition.template || null;
					if (!this.template && this.templates) {
						this.template = this.templates.root;
					}
					this.data = this.data || definition.data || {};
					this.dataSource = this.dataSource || definition.dataSource || null;

					this._rendering = false;
					this._created = false;
				}

				fetch() {
					if (!this.dataSource) {
						throw 'No source';
					}
					cv.request('GET', this.dataSource)
						.success((response) => {
							this.data = response.data;
							this.render();
						})
						.send();
				}

				select() {
					return this._node;
				}

				render() {
					if (this._rendering){ return; }
					this._rendering = true;

					if (!this._created) {
						if (ViewClass.prototype._onCreate) {
							this[ViewClass.prototype._onCreate]();
						}
						this._created = true;

						tk.listener(this, 'data')
							.changed(() => {
								this.render();
							});
					}
					
					let watch = (data, callback) => {
						if (data instanceof Array){
							if (data._watched){ return; }
							data._watched = true;
							
							tk.listener(data)
								.added((item) => {
									watch(item, callback);
									callback();
								})
								.removed((item) => {
									callback();
								});
						}
						else if (typeof data == 'object' && data !== null) {
							if (data._watched){ return; }
							data._watched = true;
				
							tk.iter(data, (property, value) => {
								if (property == '_watch'){
									return;
								}
								watch(value, callback);
								tk.listener(data, property)
									.changed((value) => {
										callback();
									});
							});
						}
					}
					let render = () => { this.render(); };
					let data = this.data;
			
					watch(this.data, render);
					watch(this.state, render);

					let el = tk.template(this.template)
						.data(this.data, this.state, this.templates)
						.render(this);

					if (ViewClass.prototype._events) {
						tk.iter(ViewClass.prototype._events, (eventDesc) => {
							el.children(eventDesc.selector).on(eventDesc.on, (tel, event) => {
								this[eventDesc.key](tel, event);
							});
						});
					}
					
					if (this._node){
						this._node.replace(el);
					}
					this._node = el;
					this.root = this._node;

					if (ViewClass.prototype._onRender) {
						this[ViewClass.prototype._onRender](el);
					}
					
					this._rendering = false;
					return this._node;
				}
			}
			
			this._viewDefinitions[name] = View;
			return View;
		}
	}

	createViews() {
		tk('cv-view').iter((el) => {
			let name = el.attr('cv-name');
			let ViewClass = this._viewDefinitions[name];
			if (!ViewClass) {
				tk.warn('No Such View: ' + name);
				return;
			}

			let label = el.attr('cv-label') || name,
				view = new ViewClass()
			this.views[label] = view;

			let create = () => {
				tk.log('Created View ' + name + ' (as ' + label + ')');
				el.replace(view.render());
			}
			
			if (view.dataSource){
				this.core.request('GET', view.dataSource)
					.success((response) => {
						view.data = response.data;
						this.core.onceReady(create);
					})
					.send();
			}
			else {
				this.core.onceReady(create);
			}
			
		});
	}

	viewEvent(on, selector) {
		if (!selector) {
			selector = on;
			on = 'click';
		}
		
		return (target, key, descriptor) => {
			target._events = target._events || [];
			target._events.push({
				selector: selector,
				on: on,
				key: key
			});
		}
	}

	viewOnCreate(target, key, descriptor) {
		target._onCreate = key;
	}

	viewOnRender(target, key, descriptor) {
		target._onRender = key;
	}
}
