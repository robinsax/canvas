class Modal {
	static rootTemplate = (createPanel) => 
		<div class="modal">
			<div class="panel" cv-event="stopPropagation">
				<i class="fa fa-times closer"></i>
				{ createPanel }
			</div>
		</div>

	constructor(params) {
		//	Parse
		this._create = params.create;
		this._bindings = params.bindings || (() => {});
		this._close = params.close || (() => {});
		this.element = null;
	}

	open() {
		let doClose = () => { this.close(); };

		this.element = tk.template(Modal.rootTemplate).data(this._create).render()
			.on('click', doClose)
			.children('.closer')
				.on('click', doClose)
			.back();

		this._bindings(this.element);

		cv.page.append(this.element);
		return this;
	}

	close() {
		if (this._close){
			this._close();
		}
		this.element.remove();
		return this;
	}
}

@loader.component
class ModalComponent {
	constructor(core) {
		core.Modal = Modal;
		
		core.modal = (params) => {
			let modal = new Modal(params);
			return modal.open();
		}
	}
}