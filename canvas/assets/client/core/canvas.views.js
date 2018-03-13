//	TODO: Async data.

class View {
	static part = null;
	static _lastName = 0;

	constructor(definition) {
		this._name = definition.name || 'component-' + (View._lastName++);
		this._target = definition.target || 'body > .page';
		this._template = definition.template;
		this._live = definition.live || false;
		this._data = definition.data || {};
		this._style = definition.style || null;
		this._binding = definition.binding || {};

		this._node = null;
	}

	_watch(data) {
		if (data instanceof Array){
			if (data._watched){
				return;
			}
			data._watched = true;
			
			tk.listener(data)
				.added((item) => {
					this._watch(item);
					this.render();
				})
				.removed((item) => {
					this.render();
				});
		}
		else if (typeof data == 'object' && data !== null) {
			if (data._watched){
				return;
			}
			data._watched = true;

			tk.iter(data, (property, value) => {
				this._watch(value);
				tk.listener(data, property)
					.changed((value) => {
						this.render();
					});
			});
		}
	}

	render(target=null) {
		//	Don't recurse if we are already in a call.
		if (this._rendering){
			return;
		}
		this._rendering = true;

		//	Maybe render as an array.
		let template = this._template;

		if (this._live){
			//	Watch data.
			this._watch(this._data);
		}

		//	Render and stuff.
		let el = tk.template(template)
			.data(this._data)
			.render();

		View._part.resolveData(el);
		el.attr('cv-view', this._name);
		tk.iter(this._binding, (selector, callback) => {
			el.children(selector).iter((el, i) => {
				callback.apply(this, [this._data, el, i]);
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
	}

	initDOM() {
		this.renderStyle();

		let rendered = this.render();
		tk(this._target).append(rendered);
	}

	renderStyle() {
		if (!this._style){
			return;
		}

		let scope = '[cv-view=' + this._name + '] ';

		let style = scope + this._style.replace(/}\s*([^$\s])/g, (match, terminator) => {
			return '} ' + scope + terminator;
		}).replace(/\s+/g, ' ');

		let el = document.createElement('style');
		el.type = 'text/css';

		if (el.styleSheet){
			el.styleSheet.cssText = style;
		}
		else {
			el.appendChild(document.createTextNode(style));
		}

		tk('head').prepend(tk(el));
	}
}

@loader.attach
class ViewPart {
	constructor(core) {
		this._dataStaging = {};
		this._dataCount = 0;

		View._part = this;
		View.define = (definition) => {
			return this.defineView(definition);
		}
		core.View = View;

		core.comp = (iterable, callback) => {
			return this.comp(iterable, callback);
		}

		//	Shim toolkit.
		tk.ToolkitSelection.prototype.data = function(){
			return this.first(false)._cvData.data;
		}
		tk.ToolkitSelection.prototype.index = function(){
			return this.first(false)._cvData.index;
		}
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
					this._dataStaging[this._dataCount++] = data;
					item.attributes['_cv-data'] = this._dataCount - 1;
				}
				result.push(item);
			}
		}
		return result;
	}

	defineView(definition) {
		return () => {
			return new View(definition);
		}
	}

	resolveData(root) {
		root.children('[_cv-data]').iter((el) => {
			let k = el.attr('_cv-data');
			let data = this._dataStaging[k + ''];

			el.attr('_cv-data', null);
			delete this._dataStaging[k];

			el.first(false)._cvData = data;
		});
	}
}