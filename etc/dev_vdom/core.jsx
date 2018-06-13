class VirtualDOMRenderer {
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
			(typeof oldVirtual == 'string' && oldNode != newVirtual) ||
			oldVirtual.tag != newVirtual.tag ||
			(newVirtual.attributes && newVirtual.attributes.forceRender)
		)
	}

	devirtualize(virtual) {
		if (!virtual) return document.createTextNode('');
		let sourceView = null;
		if (virtual instanceof viewhost.View) {
			sourceView = virtual;
			virtual = typeof virtual.template == 'function' ? virtual.template(...virtual.getRenderContext()) : virtual.template;
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

		if (sourceView) sourceView.onRender(el);
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
		else if (this.diff(newVirtual, oldVirtual)) {
			parentEl.replaceChild(this.devirtualize(newVirtual), parent.childNodes[index]);

		}
		else if (newNode.tag) {
			this.updateAttributes(parent.childNodes[index], newVirtual.attributes, oldVirtual.attributes);
			
			let maxI = Math.max(newVirtual.children.length, oldVirtual.children.length);

			for (let i = 0; i < maxI; i++) {
				try {
					this.update(parent.childNodes[index], newVirtual.children[i], oldVirtual.children[i], i);
				}
				catch (ex) {
					if (ex !== 'x') throw ex;
					i--;	//	TODO: What the fuck pt. 2.
				}
			}
		}
	}

	element(tag, attributes, ...children) {
		return {
			tag: tag,
			attributes: attributes,
			children: children
		};
	}

	render(renderable) {
		let parentEl = document.createDocumentFragment();
		this.update(parentEl, renderable, null);
		return parentEl.children[0];
	}
}


class ResourceManager {
	export(moduleName, exportMap) {
		window[moduleName] = exportMap;
	}

	loadStyle(stylesheet) {
		const importHost = document.createElement('link');
		importHost.setAttribute('type', 'text/css');
		importHost.setAttribute('rel', 'stylesheet');
		importHost.setAttribute('href', stylesheet.replace('.', '/') + '.css');
		document.getElementsByTagName('head')[0].appendChild(importHost);
	}

	import(moduleName, callback) {
		if (window[moduleName]) {
			callback();
			return;
		}
		
		const importHost = document.createElement('script');
		importHost.type = 'text/javascript';
		if (importHost.readyState) {
			importHost.onreadystatechange = () => {
				if (!(importHost.readyState === 'loaded' || importHost.readyState == 'complete')) return;

				importHost.onreadystatechange = null;
				callback();
			}
		}
		else {
			importHost.onload = callback;
		}

		importHost.setAttribute('src', moduleName.replace('.', '/') + '.js');
		document.getElementsByTagName('head')[0].appendChild(importHost);
	}
}

class ViewProvider {
	constructor() {
		class RootView {
			getRenderContext() {
				return [];
			}

			onRender(el) {}
		}

		this.View = RootView;
	}

	view(options) {
		return ViewClass => {
			class DerivedViewClass extends ViewClass {
				constructor(...args) {
					super(...args);
					this.template = options.template;
				}
			}

			let Current = DerivedViewClass.prototype;
			while (Object.getPrototypeOf(Current) !== Object.prototype) {
				Current = Object.getPrototypeOf(Current);
				if (Current === this.View.prototype) return;
			}
			
			Object.setPrototypeOf(Current, this.View.prototype);

			return DerivedViewClass;
		}
	}
}

class Utils {
	comp(iterable, transform=x => x) {
		let result = [];
		for (let i = 0; i < iterable.length; i++) {
			let item = transform(iterable[i], i);
			if (item.tag !== undefined && item.attributes !== undefined && item.children !== undefined) {
				item.attributes = result.attributes || {};
				item.attributes.boundData = iterable[i];
			}
			result.push(item);
		}
		return result;
	}
}

let renderer = new VirtualDOMRenderer();
let viewhost = new ViewProvider();
let utils = new Utils();
let resources = new ResourceManager();
