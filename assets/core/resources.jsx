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
	}
	
	export(moduleName, exportMap) {
		/* 
		*	Export the contents of `exportMap` as `moduleName`. Powers the 
		*	`::export` preprocessor directive.
		*/ 
		window[moduleName] = exportMap; 
	}

	loadStyle(stylesheet) {
		/* Load a stylesheet. Powers the `::style` preprocessor directive. */
		let path = '/assets/' + stylesheet.replace('.', '/') + '.css';
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
		//	Define completion counter and threshold.
		let importCount = 0, importTotal = moduleNames.length;
		
		//	Define a callback that invokes the callback if all imports are
		//	complete.
		const maybeFinishImport = () => {
			if (++importCount == importTotal) callback();
		}

		//	Iterate the moduels to import, importing each with a script tag.
		for (var i = 0; i < importTotal; i++) {
			let moduleName = moduleNames[i],
				//	Decide the path.
				path = '/assets/' + moduleName.replace('.', '/') + '.js';
			
			if (window[moduleName]) {
				maybeFinishImport();
				continue;
			}
			console.log(document.querySelector('script[src="' + path + '"]'))
			let importHost = document.querySelector('script[src="' + path + '"]'),
				didExist = !!importHost;
			if (!didExist) {
				importHost = document.createElement('script');
				importHost.type = 'text/javascript';
			}

			this.log.debug('Importing ' + moduleName + ' from ' + path);
			//	Create and attach the host script tag.
			if (importHost.readyState) {
				//	Legacy IE watch.
				importHost.onreadystatechange = () => {
					let state = importHost.readyState;
					if (['loaded', 'complete'].indexOf(state) < 0) return;
					
					importHost.onreadystatechange = null;
					maybeFinishImport();
				}
			}
			else {
				//	Actually good browser watch.
				importHost.addEventListener('load', maybeFinishImport);
				importHost.addEventListener('error', () => this.log.critical(
					'Failed to import "' + moduleName + '"'
				));
			}
			if (!didExist) {
				importHost.setAttribute('src', path);
			}
			document.head.appendChild(importHost);
		}
	}
}

//	Export the resource manager directly to window.
window.resources = new ResourceManager();
