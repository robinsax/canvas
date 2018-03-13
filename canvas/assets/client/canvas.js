function loadCanvas() {
	//	Define and create the core loader.
	class CoreLoader {
		constructor() {
			this.attached = [];
		}

		attach(Class){
			loader.attached.push(Class);
		}
	}
	let loader = new CoreLoader();

	//	Include directives.
	//	cv::include core/canvas.forms
	//	cv::include core/canvas.dnd
	//	cv::include core/canvas.views
	//	cv::include core/canvas.modal

	class CanvasCore {
		constructor(debug) {
			tk.config.debug = debug;
			this.debug = debug;

			let head = tk('head');
			this.route = head.attr('cv-route');
			head.attr('cv-route', null);
			
			this.query = {};

			//	Common elements.
			this.metaPage = null;
			this.page = null;

			this._registeredViews = [];
			this.views = {};

			//	Define initial actions, events, and validators.		
			this.actions = {
				redirect: (response) => { window.location.href = response.data.url; },
				refresh: (response) => {
					let refresh = (self.query.refresh || 0) + 1;
					window.location.href = window.location.pathname + '?refresh=' + refresh;
				},
				message: (response) => { this.flashMessage = response.data.message; }
			}
			this.events = {
				submit: (el, evt) => {
					let form = el.parents('form');
					if (form.empty){
						throw 'No form here';
					}
					this.form(form.attr('id')).submit();
				},
				stopPropagation: (el, evt) => { evt.stopPropagation(); }
			}
			this.validators = { 
				regex: (repr, value) => {
					repr = repr.split(':');
					let re = new RegExp(decodeURIComponent(repr[0]), repr[1] == '1' ? 'i' : '');
					return (repr[2] == '1') != re.test(value);
				},
				range: (repr, value) => {
					if (!value || value.length == 0){
						return false;
					}
					repr = repr.split(',');
					if (repr[0] != 'null'){
						min = +repr[0];
					}
					if (repr[1] != 'null'){
						max = +repr[1];
					}
					return (!min || value >= min) && (!max || value <= max);
				}
			}

			//	Load core.
			this._attached = [];
			tk.iter(loader.attached, (Class) => {
				this._attached.push(new Class(this));
			});

			//	Place initialization and inspection callbacks.
			tk.init(() => { this.init(); });
			tk.inspection((check) => { this.inspect(check); });
		}
		
		set flashMessage(message) {
			if (message && this.page){
				//	TODO(tk): Support this find or create pattern.
				let container = this.flashArea || this.page.append(tk.tag('aside', {
					class: 'flash-message'
				}));
				container.text(message).classify('hidden', false, 5000);
			}
		}

		//	Post DOM-loaded.
		init(){
			//	Grab elements.
			this.page = tk('body > .page');
			this.metaPage = tk('body > .meta');

			//	Parse query string.
			let parts = window.location.search.substring(1).split('&');
			tk.iter(parts, (part) => {
				part = part.split('=');
				this.query[decodeURIComponent(part[0])] = decodeURIComponent(part[1]);
			});

			//	Initialize attached.
			tk.iter(this._attached, (attached) => {
				if (attached.init){ attached.init(this); }
			});

			//	Create views.
			tk.iter(this._registeredViews, (view) => {
				view.initDOM();

				if (view.layout){
					tk(window).on('resize', () => {
						view.layout.apply(view);
					});
					view.layout();
				}
			});

			tk.log('canvas initialized');
		}
			
		inspect(check) {
			//	Bind events.
			check.reduce('[cv-event]')
				.iter((el) => {
					let eventName = el.attr('cv-event');
					let trigger = el.attr('cv-on') || 'click';
					
					el.on(trigger, (el, event) => {
						if (!this.events[eventName]){
							throw 'No event: ' + key;
						}
						
						this.events[eventName](el, event)
					});

					//	Consume.
					el.attr({
						'cv-event': null,
						'cv-on': null
					});
				});
				
			//	Bind actions.
			check.reduce('[cv-action]')
				.iter((el) => {
					let trigger = el.attr('cv-on') || 'click';
					el.on(trigger, () => {
						this.request
							.json({
								action: el.attr('cv-action')
							})
						.send();
					});

					el.attr('cv-on', null);
				});

			//	Open active links.
			check.reduce('a')
				.classify('open', (el) => { el.attr('href') == this.route; });

			//	Set up field classification.
			check.reduce('body > [name]')
				.off('focus')
				.off('blur')
				.on({
					focus: (el) => {
						el.parents('.field').first().classify('focused');
					},
					blur: (el) => {
						el.parents('.field').first().classify('focused', false);
					}
				});
			
			//	Set up tooltips.
			check.reduce('[cv-tooltip]')
				.iter((el) => {
					let tooltip = null;
					el.on({
						mouseover: () => { tooltip = this.tooltip(el); },
						mouseout: () => { !tooltip || tooltip.remove(); }
					});
				});
		}

		//	Decorators.
		view(condition=true) {
			return (Class) => {
				let load = (
					(typeof condition == 'boolean' && condition) ||
					(typeof condition == 'string' && condition == this.route) || 
					(typeof condition == 'function' && condition())
				);
				if (load){
					let inst = new Class();
					tk.log('Loaded view ' + Class.name);
					let name = inst.name || Class.name;
					this.views[name] = inst;
					this._registeredViews.push(inst);
				}
			}
		}
		
		action(name=null) {
			return (target, trueName) => {
				this.actions[name || trueName] = target;
			}
		}

		event(name=null) {
			return (target, trueName) => {
				this.events[name || trueName] = target;
			}
		}

		validator(name=null) {
			return (target, trueName) => {
				this.validators[name || trueName] = target;
			}
		}

		//	Send a request with defaults.
		request(method='POST', url=window.location.href) {
			return tk.request(method, url)
				.header('X-Canvas-View-Request', '1')
				.success((response) => {
					if (response.data && response.data.action){
						this.actions[response.data.action](response);
					}
				})
				.failure(() => {
					this.flashMessage = 'An error occurred'; 
				});
		}

		//	Tooltip.
		tooltip(target, content=null) {
			content = content || decodeURIComponent(target.attr('cv-tooltip'));
			if (!content){
				return;
			}

			let offset = target.offset(), 
				size = target.size(), 
				scroll = this.page.first(false).scrollTop
			
			let el = tk.tag('aside', {class: 'tooltip'}, content)
				.css({
					top: offset.y - scroll,
					left: offest.x + size.width/2 - 10
				});
			this.page.append(el);
		}
	}

	window.tk = toolkit.create();
	window.cv = new CanvasCore(tk('html').attr('cv-debug') != null);
}

loadCanvas();
