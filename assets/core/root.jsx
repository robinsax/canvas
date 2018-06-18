//	A utility used to generate the global `canvas` object at load time.

const coreComponents = [], 
	coreComponent = (X) => { 
		coreComponents.push(X); 
	},
	exposedMethod = (target, property) => {
		target[property].isExposed = true;
	};
