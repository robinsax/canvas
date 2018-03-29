@part
class ViewPart {
	static instance = null;

	constructor(core) {
		ViewPart.instance = this;
		this.core = core;

		this.dataStaging = {};
		this.dataCount = 0;

		core.views = this.views = {};

		core.view = (name, definition) => this.view(name, definition);
		core.view.event = (on, selector=null) => this.viewEvent(on, selector);
		core.view.create = (target, View) => this.createView(target, View);
		core.view.onCreate = (target, key, property) => this.viewOnCreate(target, key, property);
		core.placeViews = (routing) => this.placeViews(routing);

		tk.comp = (iterable, callback) => this.comp(iterable, callback);
		tk.ToolkitSelection.prototype.data = function(){ return this.first(false)._cvData.data; };
		tk.ToolkitSelection.prototype.index = function(){ return this.first(false)._cvData.index; };
	}

	_resolveData(root) {
		root.children('[_cv-data]').iter((el) => {
			let k = el.attr('_cv-data');
			let data = this.dataStaging[k + ''];

			el.attr('_cv-data', null);
			delete this.dataStaging[k];

			el.first(false)._cvData = data;
		});
	}

	comp(iterable, callback) {
		let result = [];
		for (let i = 0; i < iterable.length; i++){
			let item = callback(iterable[i], i);
			if (item !== undefined){
				if (item._virtual) {
					//	Attach data.
					let data = {
						data: iterable[i],
						index: i
					};
					this.dataStaging[this.dataCount++] = data;
					item.attributes['_cv-data'] = this.dataCount - 1;
				}
				result.push(item);
			}
		}
		return result;
	}

	view(name, definition) {
		return (ViewClass) => {
			class AsView extends ViewClass {
				constructor() {
					super(...arguments);
					this._name = name;
					this.state = this.state || definition.state ||  {};
					this.templates = this.templates || definition.templates || null;
					this.template = this.template || definition.template || null;
					if (!this.template && this.templates) {
						this.template = this.templates.root;
					}
					this.data = this.data || definition.data || {};

					this._rendering = false;
					this._created = false;
				}

				select() {
					return this._node;
				}

				render(target=null) {
					if (this._rendering){ return; }
					this._rendering = true;

					if (!this._created) {
						if (ViewClass.prototype._onCreate) {
							this[ViewClass.prototype._onCreate]();
						}
						this._created = true;
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
						.render();

					ViewPart.instance._resolveData(el);

					if (ViewClass.prototype._events) {
						tk.iter(ViewClass.prototype._events, (eventDesc) => {
							el.children(eventDesc.selector).on(eventDesc.on, (tel, event) => {
								this[eventDesc.key](tel, event);
							});
						});
					}
					
					if (this._node){
						if (!target){
							target = this._node.parents(false);
						}
						this._node.remove();
					}
					this._node = el;
					if (target){
						target.append(this._node);
					}
					
					this._rendering = false;
					return this._node;
				}
			}

			return AsView;
		}
	}

	createView(target, ViewClass) {
		let view = new ViewClass();
		this.views[view._name] = view;

		let create = () => {
			tk.log('Created view ' + view._name);
			view.render(tk(target));
		}
		
		if (view.dataSource) {
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
	}

	placeViews(routing) {
		tk.iter(routing, (route, definition) => {
			if (route == '*' || route == this.core.route){
				tk.iter(definition, (selector, views) => {
					tk.iter(views, (ViewClass) => {
						this.core.view.create(selector, ViewClass);
					});
				});
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
}
