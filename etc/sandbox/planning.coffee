modal = new cv.Modal
	dom: 
		'''
		<div class=".item">{{ item }}</div>
		'''
	events:
		'.item:click': (e) ->
			console.log e
		'.cancel:hover': (e) ->
			console.log e
	style:
		'.item': {
			'text-align': 'center'
		}