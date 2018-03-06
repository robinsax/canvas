function transpileES6(source){
	return require('babel-core').transform(source, {
		presets: ['es2015']
	}).code;
}

function compileCoffee(source){
	return require('coffeescript').compile(source);
}