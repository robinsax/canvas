function transpileES6(source){
	return require('babel-core').transform(source, {
		presets: ['es2015']
	}).code;
}

function compileCoffee(source){
	return transpileES6(require('coffeescript').compile(source));
}
