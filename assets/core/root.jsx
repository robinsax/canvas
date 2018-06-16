const coreComponents = [], coreComponent = (X) => { coreComponents.push(X); },
	exposedMethod = (target, property) => { target[property].isExposed = true; };
