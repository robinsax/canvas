class View {
	constructor(definition) {
		this.templates = definition.templates || null;
		this.template = definition.template || null;
		if (!this.template && this.templates) {
			this.template = this.templates.root;
		}
		this.data = definition.data || {};
		this.bindings = definition.bindings || (() => {});
		this.live = definition.live || false;
	}

	render(target=null) {
		if (this._rendering){ return; }
		this._rendering = true;
		
		let watch = (data, callback) => {
			if (data instanceof Array){
				if (data._watched){
					return;
				}
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

		if (this.live){
			watch(this.data, render);
		}

		let el = tk.template(this.template)
			.data(this.data).render();
		
		ViewPart.instance._resolveData(el);

		this.bindings(el);

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

@part
class ViewPart {
	static instance = null;

	constructor(core) {
		ViewPart.instance = this;

		this.dataStaging = {};
		this.dataCount = 0;

		core.View = View;

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
}