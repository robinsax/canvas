'use strict';
/*
*	JSX and LESS asset processor invocation. Invoked with either 'jsx' or 
*	'less' in the command line; reads processing target from stdin.
*/
const getStdIn = require('get-stdin'), babel = require('babel-core'), less = require('less');

//	Define JSX transpilation.
const transpileJSX = source => {
	return babel.transform(source, {
		presets: [
			['es2015', {
				modules: false
			}]
		],
		plugins: [
			'transform-decorators-legacy',
			['transform-react-jsx', {
				pragma: 'cv.element'
			}]
		]
	}).code;
}

//	Define less compilation.
const compileLESS = source => {
	let result = null;
	
	less.render(source, {processImports: false}, (err, res) => {
		if (err) throw err;
		result = res.css;
	});

	return result;
}

//	Read stdin.
getStdIn().then(input => {
	try {
		const which = process.argv[2];
		switch (which) {
			case 'jsx':
				console.log(transpileJSX(input));
				return;
			case 'less':
				console.log(compileLESS(input));
				return;
			default:
				throw which;
		}
	}
	catch (ex) {
		console.error(ex);
		process.exit(1);
	}
});