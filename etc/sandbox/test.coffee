babel = require 'babel-core'
coffee = require 'coffeescript'

opts =
	presets: 'es2015'
	plugins: [
		[
			'transform-react-jsx',
				pragma: 'cv.virtual'
		]
	]

src = '''
x = <div class={if condition then "asd" else "bsd"}></div>
'''

jsx = babel.transform (coffee.compile src), opts
console.log jsx.code
