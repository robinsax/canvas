let babel = require('babel-core')

function transpile(source){
	return babel.transform(source, {
		presets: [
			'es2015'
		],
		plugins: [
			'transform-decorators-legacy',
			'transform-class-properties',
			[
				'transform-react-jsx', {
					pragma: 'tk.template.tag'
				}
			]
		]
	}).code;
}
