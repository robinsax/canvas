/*
*	Generalized state encapsulation.
*/

class State {
	/*
	*	A state is an object with an associated callback that is invoked 
	*	whenever a change occurs. 
	*/
	
	constructor(initialMap) {
		/* Create a new state from a standard JavaScript map. */
		for (let key in initialMap) {
			this[key] = initialMap[key];
		}

		Object.defineProperty(this, 'callback', (() => {
			let value = null;
			
			return {
				get: () => value,
				set: (newValue) => value = newValue,
				enumerable: false
			}
		})());
	}

	observe() {
		/* Re-observe this state. */
		const callback = this.callback,
			createDescriptor = initialValue => {
				let value = initialValue;
				return {
					set: newValue => {
						value = newValue;
						callback();
					},
					get: () => value
				};
			},
			observeProperty = (object, property) => {
				if (object == this && property == 'callback') return;
				
				Object.defineProperty(object, property, 
						createDescriptor(object[property]));
			},
			observeArray = array => {
				if (array.__observed__) return;

				const updateIndicies = () => {
					for (var i = 0; i < array.length; i++) {
						observeProperty(array, i + '');
					}
				}

				array.push = (...items) => {
					Array.prototype.splice.apply(array, items);
					updateIndicies();
					callback();
				}
				array.pop = () => {
					Array.prototype.pop.apply(array);
					updateIndicies();
					callback();
				}
				array.splice = (start, count, ...items) => {
					Array.prototype.splice.apply(array, [start, count].concat(items));
					updateIndicies();
					callback();
				}

				let innerSplice = array.splice;
				
				updateIndicies();
				array.__observed__ = true;
			},
			observeObject = item => {
				if (typeof item != 'object') return;

				if (item instanceof Array) {
					observeArray(item);
				}
				else {
					let propertyNames = Object.getOwnPropertyNames(item);
					for (let i = 0; i < propertyNames.length; i++) {
						observeProperty(item, propertyNames[i]);
					}
				}
			}

		observeObject(this);

		return this;
	}

	bind(callback) {
		/* Bind this state to call `callback` on change. */
		this.callback = callback;
		
		return this;
	}

	update(updateMap={}) {
		/* Carefully update this state. */
		const updateObject = (dest, src) => {
			for (let key in src) {
				let current = dest[key], future = src[key];
				
				if (future == null || typeof current != typeof future || typeof current !=' object') {
					dest[key] = future;
				}
				else {
					updateObject(current, future);
				}
			}
		}

		updateObject(this, updateMap);
		this.observe();
		if (this.callback) {
			this.callback();
		}
	}
}

@coreComponent
class StateExposure {
	/* A trivial exposure of the `State` type. */

	constructor(core) {
		core.State = State;
	}
}