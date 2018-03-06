class Modal
	constructor: (p) ->
		#	Parse
		@createPanel = p.create
		@onClose = p.close
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

		@el.children '.panel'
			.append @createPanel()

		@

	close: () =>
		@onClose() if @onClose
		@el.remove()
		@

loader.attach class ModalMixin
	constructor: (core) ->
		core.Modal = Modal
		
		#	Modal creation.
		core.modal = (params) ->
			modal = new Modal params
			modal.open()