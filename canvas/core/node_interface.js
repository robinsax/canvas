"use strict";

let babel = require('babel-core');

function transpile(source){
	return babel.transform(source, {
		presets: [
			[
				'es2015', {
					modules: false
				}
			]
		],
		plugins: [
			'transform-decorators-legacy',
			'transform-class-properties',
			'transform-es2015-function-name',
			[
				'transform-react-jsx', {
					pragma: 'tk.template.tag'
				}
			]
		]
	}).code;
}
