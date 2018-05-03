@part
class MixinPart {
	constructor() {
		core.attachMixins = this.attachMixins.bind(this);
		core.attachMixin = this.attachMixin.bind(this);
		core.attach = core.utils.createAnnotationDecorator('isMixinAttachment');
		
		this.defineDefaultMixins();
	}

	attachMixin(instance, mixin) {
		let annotations = ['isEvent', 'isInspection'];
		if (instance instanceof core.Form) {
			annotations.push('isSuccessCallback', 'isFailureCallback');
		}

		mixin.host = instance;

		let target = Object.getPrototypeOf(instance);
		let mixinness = {};
		core.utils.iterateAnnotated(mixin, 'isMixinAttachment', prop => {
			let bound = mixin[prop].bind(mixin);
			target[prop] = target[prop] || bound;

			mixinness[prop] = bound;
		
			tk.iter(annotations, name => {
				if (mixin[prop][name]) {
					target[prop][name] = mixin[prop][name];
				}
			});
		});

		if (mixin.attach) {
			mixin.attach();
		}

		return mixinness;
	}

	attachMixins(instance, mixins) {
		tk.iter(mixins, mixin => {
			this.attachMixin(instance, mixin);
		});
	}

	defineDefaultMixins() {
		class ModalMixin {
			constructor(className=null) {
				this.className = className;
			}

			attach() {
				this.host.state.update({
					isOpen: false,
					className: this.className
				});

				let template = this.host.template;
				Object.defineProperty(this.host, 'template', (() => {
					let template = null, wrapped = false, _value = null;
					return {
						set: (value) => {
							_value = value;
							if (!wrapped) {
								template = (x, state, y) =>
									<div class={ "modal" + (state.className ? " " + state.className : "") + (state.isOpen ? " open" : "") }>
										<div class="panel">
											<i class="fa fa-times close"/>
											{ _value(x, state, y) }
										</div>
									</div>
								wrapped = true;
							}
							return value;
						},
						get: () => template,
						enumerable: true
					}
				})());
				this.host.template = template;
			}

			@core.event('.modal, .close')
			@core.onSuccess
			@core.attach
			closeModal() {
				this.host.state.isOpen = false;
			}

			@core.attach
			close() {
				this.closeModal();
			}
			
			@core.attach
			openModal() {
				this.host.state.isOpen = true;
			}

			@core.attach
			open() {
				this.openModal();
			}
			
			@core.event('.panel')
			@core.attach
			keepOpen(el, event) {
				event.stopPropagation();
			}
		}

		core.ModalMixin = ModalMixin;
	}
}