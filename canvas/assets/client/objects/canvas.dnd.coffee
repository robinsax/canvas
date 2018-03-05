class Drag
	@current: null

	constructor: (@source, params) ->
		@createElement = params.createElement ? () -> @source.copy()
		@data = params.data
		@element = null

		@source.on 'mousedown', (source, event) =>
			Drag.current?.end()
			Drag.current = @
			
			cv.page.classify
				dnd: true
				active: true

			@element = cv.page.append @createElement()
			.classify 
				dnd: true
				drag: true

			event.stopPropagation()

	end: () ->
		cv.page.classify
			dnd: false
			active: false

		Drag.current = null
		@element.remove()
		@

class Drop
	constructor: (@target, params) ->
		@accept = params.accept
		@willAccept = params.willAccept ? () -> true

		@target.on
			mouseover: (el) =>
				if Drag.current and @willAccept Drag.current
					el.classify
						dnd: true
						targeted: true
			mouseout: (el) ->
				el.classify
					dnd: false
					targeted: false
			mouseup: (el) =>
				if @willAccept Drag.current
					@accept Drag.current.end()

loader.attach class DragAndDrop
	constructor: (core) ->
		core.Drag = Drag
		core.Drop = Drop

		core.drag = (@el, params) -> 
			new Drag @el, params
		core.drop = (@el, params) ->
			new Drop @el, params
	
	init: (core) ->
		core.page.on
			mouseup: () ->
				Drag.current?.end()
			mousemove: (el, event) ->
				Drag.current?.el.css
					top: event.clientY
					left: event.clientX
