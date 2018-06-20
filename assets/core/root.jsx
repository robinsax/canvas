//	A utility used to generate the global `canvas` object at load time.

const coreComponents = [], 
	coreComponent = (X) => { 
		coreComponents.push(X); 
	},
	exposedMethod = (target, property) => {
		target[property].isExposed = true;
	};

const onceReady = callback => {
	if (['ready', 'interactive', 'complete'].indexOf(document.readyState) >= 0) {
		callback();
	}
	else {
		document.addEventListener('DOMContentLoaded', callback);
	}
}