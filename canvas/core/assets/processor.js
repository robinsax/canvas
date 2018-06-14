'use strict';
/*
*	JSX and LESS asset processor invocation. Invoked with either 'jsx' or 
*	'less' in the command line; reads processing target from stdin.
*/
const getStdIn = require('get-stdin'), debugMode = process.argv[3] == '1';

//	Define JSX transpilation.
const transpileJSX = source => {
	const babel = require('babel-core');
	let code = babel.transform(source, {
		presets: [
			['es2015', {
				modules: false
			}]
		],
		plugins: [
			'transform-decorators-legacy',
			['transform-react-jsx', {
				pragma: 'canvas.element'
			}]
		]
	}).code;

	if (!debugMode) {
		const uglifyJS = require('uglify-js');
		return uglifyJS.minify(code).code;
	}
	return code;
}

//	Define less compilation.
const compileLESS = source => {
	const less = require('less');
	let result = null, plugins = [];

	if (!debugMode) {
		const LPlCleanCSS = require('less-plugin-clean-css');
		plugins.push(new LPlCleanCSS());
	}

	less.render(source, {processImports: false, plugins: plugins}, 
		(err, res) => { if (err) throw err; result = res.css; }
	);

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