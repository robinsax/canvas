(() => {
	let _sentinel = {},
		core = null,
		parts = [];
	part = (Part) => { parts.push(Part); }

	//	cv::include core/utils
	//	cv::include core/requests
	//	cv::include core/persistance
		
	//	cv::include core/views
	//	cv::include core/validators
	//	cv::include core/forms

	//	cv::include core/mixins

	//	cv::include core/dnd
	//	cv::include core/svg
	//	cv::include core/links
	//	cv::include core/tooltip
	
	class Core {
		constructor(debug){
			core = this;
			this.debug = debug;
			this.initialized = false;
			this.readyCallbacks = [];

			let head = tk('head');
			this.route = head.attr('cv-route');
			head.attr('cv-route', null);
			
			tk.iter(parts, (Part) => new Part(this));
			
			tk.init(() => { this.initDOM(); });
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
			this.page = tk('body > div.page');
			this.header = tk('body > header.header');
			this.footer = tk('body > footer.footer');
			
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

		addInspector(callback) {
			this.onceReady(() => {
				callback(tk('body').children());
			});

			tk.inspection(callback);
		}
	}

	let debug = document.getElementsByTagName('head')[0].hasAttribute('cv-debug');
	window.tk = toolkit.create({
		debug: debug,
		iteration: {ignoreKeys: ['_watched']}
	});

	window.cv = new Core(debug);
})();
