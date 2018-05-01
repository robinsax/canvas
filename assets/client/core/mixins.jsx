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
		instance.state.update(mixin.state || {});

		let target = Object.getPrototypeOf(instance);
		core.utils.iterateAnnotated(mixin, 'isMixinAttachment', prop => {
			let bound = mixin[prop].bind(mixin);
			tk.iter(annotations, name => {
				if (mixin[prop][name]) {
					bound[name] = mixin[prop][name];
				}
			})

			target[prop] = bound;
		});

		if (mixin.attach) {
			mixin.attach();
		}
	}

	attachMixins(instance, mixins) {
		tk.iter(mixins, mixin => {
			this.attachMixin(instance, mixin);
		});
	}

	defineDefaultMixins() {
		class ModalMixin {
			constructor() {
				this.state = {
					isOpen: false,
					className: null
				};
			}

			attach() {
				let template = this.host.template;
				Object.defineProperty(this.host, 'template', (() => {
					let template = null, wrapped = false;
					return {
						set: (value) => {
							if (!wrapped) {
								template = (x, state, y) => 
									<div class={ "modal" + (state.className ? " " + state.className : "") + (state.isOpen ? " open" : "") }>
										<div class="panel">
											<i class="fa fa-times close"/>
											{ value(x, state, y) }
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
			close() {
				this.host.state.isOpen = false;
			}
			
			@core.attach
			open() {
				this.host.state.isOpen = true;
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