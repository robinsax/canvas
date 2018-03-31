@part
class SVGPart {
	constructor(core) {
		tk.inspection((el) => { this.replaceSVGs(el); });
	}

	replaceSVGs(check) {
		check.reduce('img[src]').iter((el) => {
			let src = el.attr('src');
			if (src.lastIndexOf('.svg') == src.length - 4){
				cv.request('GET', src)
					.success((svgData) => {
						let parser = new DOMParser();
						let svg = parser.parseFromString(svgData, 'text/xml')
								.getElementsByTagName('svg')[0];
						
						svg.setAttribute('class', el.classes().join(' '));
						el.replace(svg);
					}).send();
			}
		});
	}
}