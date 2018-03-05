class Form
	constructor: (@el) ->
		@submitting = false

		#	Replace submission event.
		@el.on 'submit', (el, event) =>
			@submit()
			event.preventDefault()

		#	Parse fields.
		#	TODO: More OOP
		@keys = []
		@fields = {}
		@content = {}
		@required = {}
		@validators = {}
		@validatorErrors = {}
		@errors = {}

		@fns =
			success: () -> {}
			process: () -> {}

		@el.children '[name]'
		.iter (input) =>
			name = input.attr 'name'
			@keys.push name

			setContent = (el) => @content[name] = el.value()
			input.on 
				change: setContent
				keyup: setContent

			#	Find field.
			field = input.parents '.field' 
			.first()

			#	Initialize data.
			@fields[name] = field
			@content[name] = input.value()
			@errors[name] = null
			@required[name] = null != input.attr 'required'
			
			#	Create the validation function.
			validator = input.attr 'cv-validator'
			if validator
				firstColon = validator.indexOf ':'
				type = validator.substring 0, firstColon
				typeRepr = validator.substring firstColon + 1
				@validators[name] = (value) ->
					cv.validators[type] typeRepr, value
				@validatorErrors[name] = input.attr 'cv-error'

			#	Create bindings.
			tk.binding @errors, name
			.changed (value) =>
				field.classify 'error', value != null
				.children '.error-desc'
				.html value

				return
			.begin()

			tk.binding @content, name
			.changed (value) =>
				#	Handle special cases and set on input.
				if value == '__null__'
					value = null
				else if value == null and input.is 'select'
					input.value '__null__'
				else
					input.value value

				#	Validate the field.
				@validate name, value

				#	Return value.
				value
			.begin()

	success: (callback) ->
		@fns.success = callback
		@

	process: (callback) ->
		@fns.process = callback
		@

	clear: () ->
		for name in @keys
			@content[name] = null

	populate: (source) ->
		for name, value in source
			@content[name] = value

	validate: (name=null, value=null) ->
		pass = true
		if name
			#	Validate a single field.
			value = value ? @content[name]
			if not value or (not @required[name] or not @submitting)
				@errors[name] = 'Required'
				pass = false
			else if not @validators[name] or @validators[name](value)
				@errors[name] = @validatorErrors[name]
				pass = false
			else
				@errors[name] = null
		else
			for name in @keys
				if not @validate(name)
					pass = false
		pass

	submit: () ->
		@submitting = true
		if not @validate()
			#	Dont submit un-validated forms.
			@submitting = false

		toSend = tk.unbound @content
		element = @el.children '[cv-submit-action]'
		toSend.action = element.attr 'cv-submit-action' if not element.empty
		element = @el.children '[cv-submit-url]'
		targetURL = if element.empty then cv.route else element.attr 'cv-submit-url'

		doSubmit = () =>
			toSend = @fns.process(toSend)

			cv.request 'POST', targetURL 
			.json toSend
			.success @fns.success 
			.failure (response) =>
				if response.status == 'error'
					cv.flashMessage = 'An error occurred'
					return
				
				@el.children '.error-summary' 
				.classify 'hidden', response.data.error_summary?
				.text response.data.error_summary

				for name, error in @response.data.errors
					@errors[name] = error
			.send()

			@submitting = false
		
		fileInputs = @el.children '[type="file"]'
		if fileInputs.empty
			doSubmit()
		else
			complete = 0
			cv.flashMessage = 'Uploading files...'
			fileInputs.iter (input) =>
				reader = new FileReader
				file = input.first false 
					.files[0]

				reader.onload = (event) ->
					toSend[input.attr 'name'] = 
						content: btoa event.target.result
						mimetype: file.mimetype
						filename: file.name
						_is_file: true
					if ++complete == fileInputs.length
						doSubmit()
				reader.readAsBinaryString(file)

loader.attach class Forms
	constructor: (core) ->
		@forms = {}
		@firstForm = null

		core.Form = Form
		core.form = (id=null) =>
			if id then @forms[id] else @firstForm

	init: () ->
		#	Create forms.
		tk 'form'
		.iter (el) =>
			form = new Form el
			@forms[el.attr 'id'] = form
			@firstForm = @firstForm ? form
