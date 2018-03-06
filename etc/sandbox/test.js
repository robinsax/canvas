x = require('babel-core').transform('class Foo {}', {
	presets: ['es2015']
}).code
console.log(x)