@part
class ViewPart {
	static instance = null;

	constructor(core) {
		this.dataStaging = {};
		this.dataCount = 0;

		ViewPart.instance = this;

		core.comp = (iterable, callback) => this.comp(iterable, callback);
		core.view = (definition) => this.view(definition);

		tk.ToolkitSelection.prototype.data = function(){ return this.first(false)._cvData.data; };
		tk.ToolkitSelection.prototype.index = function(){ return this.first(false)._cvData.index; };
	}

	_watch(data, callback) {
		if (data instanceof Array){
			if (data._watched){
				return;
			}
			data._watched = true;
			
			tk.listener(data)
				.added((item) => {
					this._watch(item, callback);
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
				this._watch(value, callback);
				tk.listener(data, property)
					.changed((value) => {
						callback();
					});
			});
		}
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

	view(definition) {
		definition.binding = definition.binding || {};

		return (ViewClass) => {
			ViewClass.prototype.data = function(data) {
				this.data = data;
				return this;
			};

			ViewClass.prototype.render = function(target=null) {
				if (this._rendering){
					return;
				}
				this._rendering = true;

				let render = () => { this.render(); };

				if (definition.live){
					ViewPart.instance._watch(this.data, render);
				}
		
				let el = tk.template(definition.template)
					.data(this.data).render();
				
				ViewPart.instance._resolveData(el);
		
				tk.iter(definition.binding, (selector, callback) => {
					el.children(selector).iter((el, i) => {
						callback.apply(this, [this.data, el, i]);
					});
				});
		
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
			};
		}
	}
}