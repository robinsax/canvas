@part
class MixinPart {
	constructor() {
		core.applyMixins = this.applyMixins.bind(this);

		this.defineDefaultMixins();
	}

	applyMixins(instance, mixins) {
		tk.iter(mixinClasses, mixin => {
			instance.state.update(mixin.state || {});

			tk.iter(mixin._events || [], desc => {
				let placeKey = MixinClass.name + '_' + desc.key;
				
				instance[placeKey] = mixin[desc.key];
				instance._events.push({
					key: placeKey,
					on: desc.on,
					selector: desc.selector,
					transform: desc.transform
				});
			});

			tk.iter(mixin._inspectors || [], desc => {
				let placeKey = MixinClass.name + '_' + desc.key;
				
				instance[placeKey] = mixin[desc.key];
				instance._inspectors.push({
					key: placeKey,
					selector: desc.selector
				});
			});

			if (mixin.attach) {
				mixin.attach(instance);
			}
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

			attach(instance) {
				let template = instance.template;
				Object.defineProperty(instance, 'template', (() => {
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
				instance.template = template;
			}

			@core.event('.modal, .close')
			@core.onSuccess
			close() {
				this.state.isOpen = false;
			}
			
			open() {
				this.state.isOpen = true;
			}
		
			@core.event('.panel')
			keepOpen(el, event) {
				event.stopPropagation();
			}
		}

		core.ModalMixin = ModalMixin;
	}
}