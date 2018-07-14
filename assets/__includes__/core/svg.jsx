/*
*	SVG inclusion API.
*/
//	TODO: Test fallback.
const isSVGSupported = !!(document.createElementNS && document.createElementNS('http://www.w3.org/2000/svg','svg').createSVGRect);

@coreComponent
class SVGExposure {
	/* A trivial SVG exposure */
	constructor(core) {
		@core.view({
			template: () => <div/>
		})
		class SVG {
			onceConstructed(url) {
				this.url = url;
			}
			
			onceCreated() {
				if (!isSVGSupported) {
					let image = document.createElement('img');
					image.setAttribute('src', this.url);
					this.element.parentNode.replaceChild(image, this.element);
					this.element = image;
				}
				else {
					new Request({
						url: this.url,
						success: svgData => {
							let parser = new DOMParser();
							let svg = parser.parseFromString(svgData, 'text/xml')
								.getElementsByTagName('svg')[0];
						
							this.element.parentNode.replaceChild(svg, this.element);
							this.element = svg;
						}
					});
				}
			}
		}

		core.SVG = SVG;
	}
}
