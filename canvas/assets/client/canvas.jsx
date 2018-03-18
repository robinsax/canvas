(() => {
	let parts = [];
	part = (Part) => {
		parts.push(Part);
	}

	//	cv::include core/views
	//	cv::include core/components
	//	cv::include core/dnd

	class Core {
		constructor(debug){
			this.debug = debug;
			let head = tk('head');
			this.route = head.attr('cv-route');
			head.attr('cv-route', null);
			
			this._parts = [];
			tk.iter(parts, (Part) => { this._parts.push(new Part(this)); });
			
			tk.init(() => { this.initDOM(); });
			tk.inspection(() => { this.inspectDOM(); });
			tk.log('canvas initialized');
		}

		initDOM(){
			this.page = tk('body > .page');
			
			tk.iter(this._parts, (part) => {
				if (part.initDOM){ part.initDOM(this); }
			});
		}

		inspectDOM(){
			tk.iter(this._parts, (part) => {
				if (part.inspectDOM){ part.inspectDOM(this); }
			});
		}
	}

	window.tk = toolkit.create();
	let debug = tk('head').attr('cv-debug') != null;
	tk.config.debug = debug;

	window.cv = new Core(debug);
})();
