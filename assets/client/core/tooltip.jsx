@part
class TooltipPart {
	constructor(core) {
		this.tooltipTemplate = tk.template((l, t, c) => 
			<aside class="tooltip" style={ "left: " + l + "px; top: " + t + "px;" }>{ c }</aside>
		);

		core.tooltip = (targets, content) => this.tooltip(targets, content);
	}

	tooltip(targets, content) {
		targets.on((() => {
			let tooltip = null;
			return {
				mouseover: (el) => {
					if (tooltip) { tooltip.remove(); }
					//	TODO(toolkit): Fix offset().
					let target = el.first(false).getBoundingClientRect();
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