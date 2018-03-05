class Loader
	constructor: () ->
		@components = []

	attach: (Component) ->
		@components.push Component

loader = new Loader

#	::include canvas.config
#	::include objects/canvas.forms
#	::include objects/canvas.dnd
###
class Modal
	constructor(params) ->
		@createPanel = params.create
		@onClose = params.close
		@el = null

	open: () ->
		@el = cv.page.snap '+div.modal'
		.on 'click', @close
		.snap '+div.panel'
			.on 'click', (el, event) ->
				event.stopPropagation()
			.snap '+i.fa.fa-times.closer'
				.on 'click', @close
			.back()
		.back()
		@createPanel @el.children '.panel'
		@

	close: () ->
		@onClose() if @onClose
		@el.remove()
		@
###
class CanvasCore
	constructor: ->
		#	Copy debug flag back.
		@debug = tk.config.debug

		#	Context variables.
		@route = null
		@query = {}

		#	Common elements.
		@metaPage = null
		@page = null

		#	The plugin list.
		@plugins = {}

		#	Define initial actions, events, and validators.		
		@actions = 
			redirect: (response) ->
				window.location.href = response.data.url
			refresh: (response) ->
				refresh = (self.query.refresh + 1) ? 1
				window.location.href = window.location.pathname + '?refresh=' + refresh
			message: (response) =>
				@flashMessage = response.data.message
		@events = 
			submit: (e, evt) ->
				form = e.parents 'form'
				throw 'No form here' if form.empty 

				@form(form.attr 'id').submit()
			end: (e, evt) ->
				evt.stopPropagation()
		@validators = 
			regex: (repr, value) ->
				repr = repr.split ':'
				re = new Regex decodeURIComponent(repr[0]), if repr[1] == '1' then 'i' else ''
				negative = repr[2] == '1'
				negative != re.test value
			range: (repr, value)->
				if not val or value.length == 0
					false
				repr = repr.split ','
				if repr[0] != 'null'
					min = +repr[0]
				if repr[1] != 'null'
					max = +repr[1]
				(!min or value >= min) and (!max or value <= max)

		#	Create magic objects.
		@flashMessage = null
		tk.binding @, 'flashMessage'
			.changed (value) ->
				if value and @page
					@page.snap '+*aside.flash-message.hidden'
					.text value
					.classify 'hidden', false, 5000

				return
			.begin()

		#	Load components.
		@components = []
		for Component in loader.components
			@components.push(new Component @)

		#	Place initialization and inspection callbacks.
		tk.init () => 
			@init()
		tk.inspection () =>
			@inspect()
	
	init: ->
		#	Initialize own fields.
		@route = tk 'html' 
		.attr 'cv-route'

		#	Grab elements.
		@page = tk 'body > .page'
		@metaPage = tk 'body > .meta'

		#	Parse query string.
		parts = window.location.substring 1
		.split '&'
		for part in parts
			part = parts.split '='
			self.query[decodeURIComponent part[0]] = decodeURIComponent part[1] 

		#	Initialize components.
		for component in @components
			component.init?(core)

		#	Initialize plugins.
		for plugin in @plugins

			#	Resolve decorators.
			for property, value in plugin
				if value._target?
					value._target[value._name] = value

			#	Initialize.
			plugin.init()

	inspect: (check) =>
		#	Bind events.
		check.reduce '[cv-event]'
		.iter (el) =>
			eventName = el.attr 'cv-event'
			trigger = el.attr 'cv-on' ? 'click'
			
			el.on trigger, (el, event) =>
				if not @events[eventName]? 
					throw 'No event: ' + key
				
				@events[eventName](el, event)
		
		#	Bind actions.
		check.reduce '[cv-action]'
		.iter (el) =>
			el.on el.attr 'cv-on' ? 'click', () =>
				@request
				.json
					action: el.attr('cv-action')
				.send()

		#	Open active links.
		check.reduce 'a'
		.classify 'open', (el) =>
			el.attr 'href' == @route

		#	Set up field classification.
		check.reduce 'body > [name]'
		.off 'focus'
		.off 'blur'
		.on
			focus: (el) ->
				el.parents '.field'
				.classify 'focused'
			blur: (el) ->
				el.parents '.field'
				.classify 'focused', false
		
		#	Set up tooltips.
		check.reduce '[cv-tooltip]'
		.iter (el) =>
			tooltip = null
			el.on
				mouseover: () =>
					tooltip = @tooltip el
				mouseout: () ->
					tooltip.remove() if tooltip

	plugin: (PluginClass, condition) ->
		if (typeof condition == 'boolean' and condition) or
				(typeof condition == 'string' and tk('html').attr('cv-route') == condition) or 
				(typeof condition == 'function' and condition())
			#	Condition passed, load and store plugin.
			inst = new PluginClass
			name = inst.name ? tk.fname PluginClass
			@plugins[name] = inst

	#	Define decorators.
	_decorate: (func, name, target) ->
		func._name = name ? tk.fname func
		if name
			target[func._name] = func
		else
			func._target = target

	action: (func, name=null) ->
		_decorate(func, name, @actions)
	
	event: (func, name=null) ->
		_decorate(func, name, @events)

	validator: (func, name=null) ->
		_decorate(func, name, @validators)

	#	Modal creation.
	modal: (params) ->
		modal = new Modal params
		modal.open()

	#	Send a request with defaults.
	request: (method='POST', url=window.location.href) ->
		flashError = () => @flashMessage = 'An error occurred'

		tk.request method, url
		.header 'X-Canvas-View-Request', '1'
		.success (response) =>
			if response.data?.action?
				@actions[response.data.action](response);
		.failure flashError
		.error flashError

	#	Create and return a tooltip element on target.
	tooltip: (target, content=null) ->
		content = content ? decodeURIComponent target.attr 'cv-tooltip'
		if not content
			return

		offset = target.offset()
		size = target.size()
		scroll = @page.first(false).scrollTop
		
		@page.snap '+aside.tooltip'
		.css
			top: offset.y - scroll
			left: offest.x + size.width/2 - 10
		.text content

window.tk = createToolkit
	debug: true

window.cv = new CanvasCore
