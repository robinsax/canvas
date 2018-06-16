/*
*	The virtual DOM and view API implementation.
*/

@coreComponent
class VirtualDOMRenderer {
	constructor(core) {
		this.core = core;
		this.log = core.logger('vdr');
		this.renderStack = [];
		VirtualDOMRenderer.instance = this;
	}

	@exposedMethod
	comp(data, callback) {
		for (var i = 0; i < data.length; i++) {
			let result = callback(data[i], i);
			if (result.tag && result.attributes && result.children) {
				result.data = data[i];
				result.index = i;
			}
		}
	}

	flatten(iterable) {
		while (true) {
			let verifiedFlat = true, pass = [];

			for (let i = 0; i < iterable.length; i++) {
				let item = iterable[i];
				if (item instanceof Array) {
					pass = pass.concat(item);
					verifiedFlat = false;
				}
				else {
					pass.push(item);
				}
			}

			if (verifiedFlat) return pass;
		}
	}

	diff(oldVirtual, newVirtual) {
		return (
			(typeof oldVirtual != typeof newVirtual) ||
			(typeof oldVirtual == 'string' && oldVirtual != newVirtual) ||
			oldVirtual.tag != newVirtual.tag ||
			(newVirtual.attributes && newVirtual.attributes.forceRender)
		)
	}

	devirtualize(virtual) {
		if (!virtual) return document.createTextNode('');
		if (virtual instanceof this.core.View) {
			virtual = virtual.template(...virtual.getRenderContext());
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
				else if (attr == 'boundData') {
					el.__data__ = value;
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
		}

		return el;
	}

	updateAttributes(targetEl, oldAttrs, newAttrs) {
		for (let attr in oldAttrs) {
			if (!oldAttrs[attr] || oldAttrs[attr] != newAttrs[attr]) return;

			targetEl.setAttribute(attr, newAttrs[attr]);
		}
		for (let attr in oldAttrs) {
			if (!newAttrs[attr]) return;
			
			targetEl.removeAttribute(attr);
		}
	}

	update(parentEl, newVirtual, oldVirtual, index=0) {
		if (!oldVirtual) {
			parentEl.appendChild(this.devirtualize(newVirtual));
		}
		else if (!newVirtual) {
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
			this.updateAttributes(parentEl.childNodes[index], newVirtual.attributes, oldVirtual.attributes);
			
			let maxI = Math.max(newVirtual.children.length, oldVirtual.children.length);

			for (let i = 0; i < maxI; i++) {
				try {
					this.update(parentEl.childNodes[index], newVirtual.children[i], oldVirtual.children[i], i);
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
			children: children
		};
	}

	@exposedMethod
	render(view) {
		this.renderStack.push(view);
		if (!(view instanceof View)) {
			let parentEl = document.createDocumentFragment();
			this.update(parentEl, view, null);
			return parentEl.children[0];
		}
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
		
		this.core.observeState(view);

		this.renderStack.pop();
		return view.element = parentEl.children[index];
	}
}
