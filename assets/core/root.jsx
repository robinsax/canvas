//	Create a decorator for collection the set of core components and an 
//	exposure flag decorator.
const coreComponents = [], coreComponent = (X) => { coreComponents.push(X); },
	exposedMethod = (target, property) => { target[property].isExposed = true; };
