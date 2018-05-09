@part
class TooltipPart {
	constructor(core) {
		this.tooltipTemplate = tk.template((l, t, c) => 
			<aside class="tooltip" style={ "left: " + l + "px; top: " + t + "px;" }>{ c }</aside>
		);

		core.tooltip = (targets, content) => this.tooltip(targets, content);

		class TooltipMixin {
			constructor(map) {
				this.map = map;
			}
		
			@core.inspects('*')
			@core.attach
			tmMaybeAttachTooltip(el) {
				tk.iter(this.map, (selector, tooltip) => {
					if (el.is(selector)) {
						core.tooltip(el, tooltip);
					}
				});
			}
		}
		
		core.TooltipMixin = TooltipMixin;
	}

	tooltip(targets, content) {
		targets.on((() => {
			let tooltip = null;
			return {
				mouseover: (el) => {
					if (tooltip) { tooltip.remove(); }
					//	TODO(toolkit): Fix offset().
					let target = el.first(false).getBoundingClientRect();
					if (typeof content == 'function') {
						content = content(el);
					}
					
					tooltip = this.tooltipTemplate
						.data(target.x, target.y, content)
						.render();
					return tk('body').append(tooltip);
				},
				mouseout: (el) => {
					tooltip.remove();
					tooltip = null;
				}
			}
		})());
	}
}