"use strict";

let babel = require('babel-core');
let fs = require('fs');

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
			[
				'transform-react-jsx', {
					pragma: 'renderer.element'
				}
			]
		]
	}).code;
}

fs.writeFileSync(process.argv[3], transpile(fs.readFileSync(process.argv[2])));
