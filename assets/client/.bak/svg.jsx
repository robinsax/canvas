@part
class SVGPart {
	constructor() {
		this.cache = {};

		core.addInspector((check) => {
			this.replaceSVGs(check);
		});
	}

	replaceSVGs(check) {
		check.reduce('cv-svg').iter((el) => {
			let src = el.attr('src');
			let swap = (svgData) => {
				let parser = new DOMParser();
				let svg = parser.parseFromString(svgData, 'text/xml')
						.getElementsByTagName('svg')[0];
			
				svg.setAttribute('class', el.classes().join(' '));
				el.replace(svg);
			}

			if (src.lastIndexOf('.svg') == src.length - 4){
				if (this.cache[src]){
					swap(this.cache[src]);
				}
				else {
					core.request('get', src)
						.success((svgData) => {
							this.cache[src] = svgData;
							swap(svgData);
						}).send();
				}
			}
		});
	}
}
