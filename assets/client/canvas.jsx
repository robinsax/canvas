(() => {
	let parts = [];
	part = (Part) => {
		parts.push(Part);
	}

	//	cv::include core/requests
	//	cv::include core/views
	//	cv::include core/dnd

	class Core {
		constructor(debug){
			this.debug = debug;
			this.initialized = false;
			this.readyCallbacks = [];

			let head = tk('head');
			this.route = head.attr('cv-route');
			head.attr('cv-route', null);
			
			this._parts = tk.comp(parts, (Part) => new Part(this));
			
			tk.init(() => { this.initDOM(); });
			tk.inspection(() => { this.inspectDOM(); });
			tk.log('canvas initialized');
		}

		set flashMessage(message) {
			let el = tk.tag('aside', {class: 'flash-message'}, message);
			tk('body').append(el);
			tk.timeout(4000, () => {
				el.remove();
			});
		}

		initDOM(){
			this.initialized = true;
			this.page = tk('body > .page');
			this.header = tk('body > .header');
			
			tk.iter(this.readyCallbacks, (callback) => {
				callback();
			});
		}

		onceReady(callback) {
			if (this.initialized){
				callback();
			}
			else {
				this.readyCallbacks.push(callback);
			}
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