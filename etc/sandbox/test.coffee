view = new cv.View
	name: 'myView'
	templates:
		item1: (item) ->
			<div class="fridge">{ 'illn template ' + item.label }</div>
	data: () ->
		cv.request()
			.json
				action: 'get_data'
