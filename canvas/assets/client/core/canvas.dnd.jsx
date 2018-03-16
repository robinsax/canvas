class Drag {
	static current = null;

	constructor(source, params) {
		this.source = source;
		this._displayed = params.displayed || (() => { return this.source.copy() });
		this._data = params.data;
		this.dataSource = params.dataSource;
		this.element = null;

		this.source
			.classify({
				dnd: true,
				target: true
			})
			.on('mousedown', (ignored, event) => {
				if (Drag.current){
					Drag.current.end();
				}
				Drag.current = this;

				cv.page.classify({
					dnd: true,
					active: true
				});
				this.element = cv.page.append(this._displayed())
					.classify({
						dnd: true,
						drag: true
					});
				let size = this.element.size();
				this.element.css({
					top: event.clientY - size.height/2,
					left: event.clientX - size.width/2
				});

				event.preventDefault();
			});
	}

	get data(){
		if (this._data){
			return this._data;
		}
		else if (this.dataSource){
			return this.dataSource();
		}
		throw 'No data!';
	}

	end() {
		cv.page.classify({
			dnd: false,
			active: false
		});

		Drag.current = null;
		this.element.remove();
		return this;
	}
}

class Drop {
	constructor(target, params){
		this.target = target;
		this.accept = params.accept;
		this.accepts = params.accepts || (() => { return true; });

		this.target.on({
			mouseover: (el) => {
				if (Drag.current && this.accepts(Drag.current)){
					el.classify({
						dnd: true,
						targeted: true
					});
				}
			},
			mouseout: (el) => {
				el.classify({
					dnd: false,
					targeted: false
				});
			},
			mouseup: (el) => {
				if (Drag.current != null){
					if (this.accepts(Drag.current)){
						this.accept(Drag.current.end().data);
					}
				}
			}
		});
	}
}

@loader.attach
class DragAndDropPart {
	constructor(core) {
		core.Drag = Drag;
		core.Drop = Drop;

		core.drag = (el, params) => { return new Drag(el, params); };
		core.drop = (el, params) => { return new Drop(el, params); };
	}
	
	init(core) {
		core.page.on({
			mouseup: () => {
				if (Drag.current != null){
					Drag.current.end();
				}
			},
			mousemove: (el, event) => {
				if (Drag.current != null){
					let el = Drag.current.element, size = el.size();
					el.css({
						top: event.clientY - size.height/2,
						left: event.clientX - size.width/2
					});
				}
			}
		});
	}
}