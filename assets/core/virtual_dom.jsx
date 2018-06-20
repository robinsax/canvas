/*
*	The virtual DOM implementation.
*/

@coreComponent
class VirtualDOMRenderer {
	/* The virtual DOM renderer and exposure. */

	constructor(core) {
		this.log = new Logger('vdr');
		this.renderStack = [];
		this.renderBatch = [];

		//	The View faculties require a reference to this render.
		VirtualDOMRenderer.instance = this;
	}

	@exposedMethod
	comp(data, callback) {
		/*
		*	Perform a comprehension on `data` that allows data-DOM binding if
		*	the result items are JSX snippets.
		*/
		let results = [];
		for (var i = 0; i < data.length; i++) {
			let result = callback(data[i], i);
			if (result.tag && result.attributes && result.children) {
				result.data = data[i];
				result.index = i;
			}
			results.push(result);
		}

		return results;
	}

	flatten(iterable) {
		/* Flatten an iterable with constituent iterables. */
		let input = iterable;
		while (true) {
			let verifiedFlat = true, pass = [];
			for (let i = 0; i < input.length; i++) {
				let item = input[i];
				if (item instanceof Array) {
					pass = pass.concat(item);
					verifiedFlat = false;
				}
				else {
					pass.push(item);
				}
			}

			if (verifiedFlat) return pass;
			input = pass;
		}
	}

	diff(oldVirtual, newVirtual) {
		return (
			(typeof oldVirtual != typeof newVirtual) ||
			(
				['string', 'number'].indexOf(typeof oldVirtual) >= 0 && 
				oldVirtual != newVirtual
			) ||
			oldVirtual.tag != newVirtual.tag ||
			(newVirtual.attributes && newVirtual.attributes.forceRender)
		)
	}

	hydrateElement(el, virtual) {
		//	TODO: Use for rehydration.
		if (el.__listeners__) {
			for (let i = 0; i < el.__listeners__.length; i++) {
				let listener = el.__listeners__[i];
				el.removeEventListener(listener.selector, listener.listener);
			}
		}

		el.__listeners__ = [];
		let currentView = this.renderStack[this.renderStack.length - 1],
			checkEvents = currentView.__events__ || [];
		for (var i = 0; i < checkEvents.length; i++) {
			let checkEvent = checkEvents[i];
			if (!el.matches(checkEvent[0])) continue;

			let listener = event => {
				let context = {element: el, event: event};
				let cur = el;
				while (cur && cur != document) {
					if (cur.__data__) {
						context.data = cur.__data__;
						context.index = cur.__index__;
						break;
					}
					cur = cur.parentNode;
				}
				currentView[checkEvent[2]](context);
			};

			el.__listeners__.push({
				listener: listener,
				selector: checkEvent[1]
			});
			el.addEventListener(checkEvent[1], listener);
		}
	}

	devirtualize(virtual) {
		if (virtual == undefined || virtual == null) return document.createTextNode('');
		if (virtual instanceof View) {
			let view = virtual;
			let parentView = this.renderStack[this.renderStack.length - 1];
			if (parentView) {
				view.attachToParent(parentView);
				view.parent = parentView;
			}
			return this.render(view);
		}

		let el = null;
		if (typeof virtual == 'string' || typeof virtual == 'number') {
			el = document.createTextNode(virtual + '');
		}
		else if (typeof virtual == 'function') {
			el = this.devirtualize(virtual());
		}
		else if (virtual instanceof Array) {
			let devirtualized = [];
			for (let i = 0; i < virtual.length; i++) {
				devirtualized.push(this.devirtualize(virtual[i]));
			}
			el = devirtualized;
		}
		else {
			el = document.createElement(virtual.tag);
			
			for (let attr in virtual.attributes) {
				let value = virtual.attributes[attr];
				if (attr === 'safeHTML') {
					el.innerHTML = value;
				}
				else {
					el.setAttribute(attr, value);
				}
			}

			if (virtual.data) {
				el.__data__ = virtual.data;
				el.__index__ = virtual.index;
			}

			if (virtual.children.length > 0) {
				for (let i = 0; i < virtual.children.length; i++) {
					let childEl = this.devirtualize(virtual.children[i]);
					if (childEl instanceof Array) {
						for (var j = 0; j < childEl.length; j++) {
							el.appendChild(childEl[j]);
						}
					}
					else {
						el.appendChild(childEl);
					}
				}
			}

			this.hydrateElement(el, virtual);
		}

		return el;
	}

	updateAttributes(targetEl, newAttrs, oldAttrs) {
		for (let attr in newAttrs) {
			targetEl.setAttribute(attr, newAttrs[attr]);
		}

		for (let attr in oldAttrs) {
			if (newAttrs[attr]) return;
			
			targetEl.removeAttribute(attr);
		}
	}

	update(parentEl, newVirtual, oldVirtual, index=0) {
		if (newVirtual instanceof View){
			//	TODO: This is a hotfix. onceCreated should never be invoked for
			//	these throwaway views.
			newVirtual.onceCreated = () => {}
		}


		if (oldVirtual === undefined || oldVirtual === null) {
			parentEl.appendChild(this.devirtualize(newVirtual));
		}
		else if (newVirtual === undefined || newVirtual === null) {
			if (parentEl.childNodes[index]) {
				parentEl.removeChild(parentEl.childNodes[index]);
				throw 'x';	//	TODO: What the fuck.
			}
		}
		else if (oldVirtual instanceof View) {
			this.render(oldVirtual);
		}
		else if (this.diff(newVirtual, oldVirtual)) {
			parentEl.replaceChild(
				this.devirtualize(newVirtual), parentEl.childNodes[index]
			);
		}
		else if (newVirtual.tag) {
			let el = parentEl.childNodes[index];
			this.updateAttributes(el, newVirtual.attributes, oldVirtual.attributes);
			
			if (newVirtual.data) {
				el.__data__ = newVirtual.data;
				el.__index__ = newVirtual.index;
			}

			let maxI = Math.max(newVirtual.children.length, oldVirtual.children.length);

			for (let i = 0; i < maxI; i++) {
				try {
					this.update(el, newVirtual.children[i], oldVirtual.children[i], i);
				}
				catch (ex) {
					if (ex !== 'x') throw ex;
					i--;	//	TODO: What the fuck pt. 2.
				}
			}
		}
	}

	@exposedMethod
	element(tag, attributes, ...children) {
		return {
			tag: tag,
			attributes: attributes,
			children: this.flatten(children)
		};
	}

	@exposedMethod
	render(view) {
		if (!(view instanceof View)) {
			let parentEl = document.createDocumentFragment();
			this.update(parentEl, view, null);
			return parentEl.children[0];
		}

		this.renderStack.push(view);
		let parentEl, index = 0;
		if (view.element) {
			parentEl = view.element.parentNode;
			for (var i = 0; i < parentEl.children.length; i++) {
				if (parentEl.children[i] == view.element) {
					index = i;
					break;
				}
			}
		}
		else {
			parentEl = document.createDocumentFragment();
		}

		let newDOM = view.template(...view.getRenderContext());
		this.update(parentEl, newDOM, view.referenceDOM, index);
		view.referenceDOM = newDOM;
		
		view.state.bind(view.render.bind(view));

		this.renderBatch.push(view);
		this.renderStack.pop();
		view.element = parentEl.children[index];
		view.element.__view__ = view;
		view.state.observe();

		if (this.renderStack.length == 0) {
			while (this.renderBatch.length > 0) {
				let next = this.renderBatch.pop();
				if (next && !next.created) {
					next.created = true;
					next.onceCreated();
				}
			}
		}

		return view.element;
	}
}
