'use strict';
/*
*	JSX and LESS asset processor invocation. Invoked with either 'jsx' or 
*	'less' in the command line; reads processing target from stdin.
*/
const babel = require('babel-core'), less = require('less');

//	Define JSX transpilation.
const transpileJSX = source =>
	babel.transform(source, {
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

//	Define less compilation.
const compileLESS = source => {
	const parser = new less.Parser({processImports: false});
	let result = null;

	lessParser.parse(source, (err, res) => {
		if (err) throw err;
		result = res;
	});

	return result;
}

//	Read stdin.
let input = [];
process.stdin.on('data', chunk => { input.push(chunk) });

//	Invoke the approprate processor once input is ready.
process.stdin.on('end', ((which, input) => {
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
})(process.argv[2], input.join('')));
