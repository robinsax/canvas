babel = require 'babel-core'

opts =
	presets: 'es2015'
	plugins: [
		[
			'transform-react-jsx',
				pragma: 'cv.tag'
		]
	]

jsx = babel.transform 'x = <div class="asd"></div>', opts
console.log jsx.code
