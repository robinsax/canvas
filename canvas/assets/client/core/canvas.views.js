class View {
	constructor(parameters) {
		this.template = parameters.template || null;
		this.target = parameters.target || 'body > .page';
		this.data = parameters.data || null;
		this.array = parameters.array || false;
		this.live = parameters.live || false;
		this.dataSource = parameters.dataSource || null;
		this.bindings = parameters.bindings || (() => {});
		this._rendering = false;

		this.node = null;
	}

	_watch(data) {
		if (data instanceof Array){
			tk.listener(data)
				.added((item) => {
					this._watch(data);
					this.render();
				})
				.removed((item) => {
					this.render();
				});
		}
		else {
			tk.iter(data, (property, value) => {
				if (value instanceof Array || typeof value == 'object'){
					this._watch(value);
				}
				tk.listener(data, property)
					.changed((value) => {
						this.render();
					});
			});
		}
	}

	render() {
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

		//	Prolly fukt, as I am.
		if (this.node){
			let before = this.node.prev();
			this.node.remove();
			if (before.empty){
				this.node = this.node.parents(false).prepend(this.node);
			}
			else {
				this.node.remove();
				before.next(el);
				this.node = el;
			}
		}
		else {
			this.node = tk(this.target).append(el);
		}
		this._rendering = false;
	}
}

@loader.component
class ViewsComponent {
	constructor(core) {
		core.View = View;

		core.view = (params) => {
			let view = new View(params);
			view.render();
			return view;
		}
	}
}