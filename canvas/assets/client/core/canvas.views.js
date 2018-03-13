class View {
	constructor(parameters) {
		this.template = parameters.template || null;
		this.data = parameters.data || null;
		this.array = parameters.items || false;
		this.live = parameters.live || false;
		this.dataSource = parameters.dataSource || null;
		this.bindings = parameters.bindings || (() => {});
		this._rendering = false;

		this.node = null;
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
		else if (typeof data == 'object') {
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
		//	Fetch data if it's remote.
		if (this.data == null && this.dataSource != null){
			this.dataSource.success((response) => {
				this.data = response.data;
				this.render();
			}).send();
			return;
		}

		//	Don't recurse if we are already in a call.
		if (this._rendering){
			return;
		}
		this._rendering = true;

		//	Maybe render as an array.
		let template = this.template;
		if (this.array){
			template = (data) => data.map(this.template);
		}

		if (this.live){
			//	Watch data.
			this._watch(this.data);
		}

		//	Render.
		let el = tk.template(template)
			.data(this.data)
			.render();
		
		this.bindings(el);

		if (this.node){
			if (!target){
				target = this.node.parents(false);
			}
			this.node.remove();
		}
		this.node = el;
		if (target){
			target.append(this.node);
		}
		this._rendering = false;
		return this.node;
	}
}

@loader.component
class ViewsComponent {
	constructor(core) {
		core.View = View;

		core.view = (params) => {
			let view = new View(params);
			return view.render();
		}
	}
}