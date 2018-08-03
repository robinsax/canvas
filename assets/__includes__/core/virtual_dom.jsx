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
	comp(data, callback, start=0, end=-1) {
		/*
		*	Perform a comprehension on `data` that allows data-DOM binding if
		*	the result items are JSX snippets.
		*/
		let results = [];
		if (!data) return results;
		if (typeof data == 'number') {
			data = {length: data};
		}

		for (var i = start; i < data.length && (end < 0 || i < end); i++) {
			let result = callback(data[i], i);
			if (result === undefined) continue;

			if (result.tag !== undefined && result.attributes !== undefined && result.children !== undefined) {
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

	hydrateElement(el, virtual, wasCreated=false) {
		if (this.renderStack.length == 0) return;
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
		const findData = cur => {
			while (cur && cur != document) {
				if (cur.__data__ !== undefined) return cur
				
				cur = cur.parentNode;
			}
			return null;
		}

		for (var i = 0; i < checkEvents.length; i++) {
			let checkEvent = checkEvents[i];
			if (!el.matches(checkEvent[0])) continue;

			if (checkEvent[1] == 'create' && wasCreated) {
				currentView[checkEvent[2]]({element: el});
				continue;
			}

			let listener = event => {
				event.keyCode = event.keyCode || event.which;
				let context = {element: el, event: event},
					dataHost = findData(el);
				if (dataHost) {
					context.dataAbove = (start => () => findData(start))(dataHost.parentNode);
					context.data = dataHost.__data__;
					context.index = dataHost.__index__;
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
				if (value === null || value === undefined) continue;

				if (attr === 'dangerous-markup') {
					el.innerHTML = value;
				}
				else {
					el.setAttribute(attr, value);
				}
			}

			if (virtual.data !== undefined) {
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

			this.hydrateElement(el, virtual, true);
		}

		return el;
	}

	updateAttributes(targetEl, newAttrs, oldAttrs) {
		for (let attr in newAttrs) {
			if (attr == 'dangerous-markup') {
				targetEl.innerHTML = newAttrs[attr];
			}
			else {
				targetEl.setAttribute(attr, newAttrs[attr]);
			}
		}

		for (let attr in oldAttrs) {
			if (newAttrs[attr]) return;
			
			targetEl.removeAttribute(attr);
		}
	}

	isNothing(x) {
		return x === undefined || x === null;
	}

	update(parentEl, newVirtual, oldVirtual, index=0) {
		if (newVirtual instanceof View){
			//	TODO: This is a hotfix. onceCreated should never be invoked for
			//	these throwaway views.
			newVirtual._onceCreated = newVirtual.onceCreated;
			newVirtual.onceCreated = () => {}
		}

		if (this.isNothing(oldVirtual) && !this.isNothing(newVirtual)) {
			parentEl.appendChild(this.devirtualize(newVirtual));
		}
		else if (this.isNothing(newVirtual)) {
			if (parentEl.childNodes[index]) {
				parentEl.removeChild(parentEl.childNodes[index]);
				throw 'x';	//	TODO: What the fuck.
			}
		}
		else if (oldVirtual instanceof View) {
			if (!oldVirtual.hasChanged(newVirtual)) {
				this.render(oldVirtual);
			}
			else {
				if (!oldVirtual.element) return;
				
				//	TODO: Sometimes oldVirtual is destroyed before it is created & sometimes it isnt called.
				oldVirtual.beforeDestroyed(newVirtual);
				newVirtual.onceCreated = newVirtual._onceCreated;
				let parentView = this.renderStack[this.renderStack.length - 1];
				if (parentView) {
					newVirtual.attachToParent(parentView);
					newVirtual.parent = parentView;
				}
				parentEl.replaceChild(this.render(newVirtual), oldVirtual.element);
			}
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
			let root = document.createDocumentFragment();
			this.update(root, view, null);
			return root.children[0];
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
		
		view.processState();
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
