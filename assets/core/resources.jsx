/*
*	The client resource manager implements canvas's import and export system,
*	as well as utilities for stylesheet inclusion directly from JavaScript 
*	files to make component style organization more managable.
*
*	Resource management should generally be defined via pre-processor 
*	directives, which resolve to calls to methods of the global
*	`ResourceManager` instance, `resources`.
*/

class ResourceManager {
	/* The singleton resource manager class. */

	constructor() {
		this.log = new Logger('resources');

		this.importQueue = [];
	}
	
	export(moduleName, exportMap) {
		/* 
		*	Export the contents of `exportMap` as `moduleName`. Powers the 
		*	`::export` preprocessor directive.
		*/ 
		window[moduleName] = exportMap;
		this.processImports();
	}

	processImports() {
		for (let i = 0; i < this.importQueue.length; i++) {
			let importItem = this.importQueue[i];
			let done = true;
			//	Check library imports.
			for (let j = 0; j < importItem.libs.length; j++) {
				let hostCheck = importItem.libs[j];
				if (!hostCheck()) {
					done = false;
					break;
				}
			}
			if (!done) continue;
			//	Check module imports.
			for (let j = 0; j < importItem.modules.length; j++) {
				if (!window[importItem.modules[j]]) {
					done = false;
					break;
				}
			}
			if (!done) continue;
			
			setTimeout(importItem.callback, 1);
			this.importQueue.splice(i, 1);
			i--;
		}
	}

	loadStyle(stylesheet) {
		/* Load a stylesheet. Powers the `::style` preprocessor directive. */
		let path = '/assets/' + stylesheet.replace('.', '/') + '.css';
		if (document.querySelector('link[href="' + path + '"]')) return;

		this.log.debug('Loading stylesheet ' + path);
		//	Create and attach the element.
		let importHost = document.createElement('link');
		importHost.setAttribute('type', 'text/css');
		importHost.setAttribute('rel', 'stylesheet');
		importHost.setAttribute('href', path);
		document.head.appendChild(importHost);
	}

	import(moduleNames, callback) {
		/* 
		*	Import a set of modules by name, invoking `callback` once they are 
		*	available. This powers the `::import` preprocess directive.
		*/
		let importItem = {
			modules: [],
			libs: [],
			callback: callback
		};
		this.importQueue.push(importItem);

		//	Iterate the moduels to import.
		for (var i = 0; i < moduleNames.length; i++) {
			let moduleName = moduleNames[i];

			//	Decide the path.
			let path, isLibrary = moduleName[0] == '!';
			if (isLibrary) {
				path = '/assets/' + moduleName.substring(1) + '.js';
			}
			else {
				path = '/assets/' + moduleName.replace('.', '/') + '.js';
				importItem.modules.push(moduleName);
			}
			
			if (document.querySelector('script[src="' + path + '"]')) continue;
			
			let importHost = document.createElement('script');
			importHost.type = 'text/javascript';
			this.log.debug('Importing ' + moduleName + ' from ' + path);
			
			//	Create and attach the host script tag.
			if (importHost.readyState) {
				//	Legacy IE watch.
				importHost.onreadystatechange = () => {
					let state = importHost.readyState;
					if (['loaded', 'complete'].indexOf(state) < 0) return;
					
					importHost.onreadystatechange = null;
					this.processImports();
				}
				if (isLibrary) {
					importItem.libs.push(importHost);
				}
			}
			else {
				//	Actually good browser watch.
				if (isLibrary) {
					importItem.libs.push(() => false);
					let k = importItem.libs.length - 1;
					importHost.addEventListener('load', () => {
						importItem.libs[k] = () => true;
						this.processImports();
					});
				}
				importHost.addEventListener('error', () => this.log.critical(
					'Failed to import "' + moduleName + '"'
				));
			}

			importHost.setAttribute('src', path);
			document.head.appendChild(importHost);
		}

		this.processImports();
	}
}

//	Export the resource manager directly to window.
window.resources = new ResourceManager();
