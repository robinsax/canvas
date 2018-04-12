@part
class SVGPart {
	constructor(core) {
		this.core = core;

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
					this.core.request('GET', src)
						.success((svgData) => {
							this.cache[src] = svgData;
							swap(svgData);
						}).send();
				}
			}
		});
	}
}
