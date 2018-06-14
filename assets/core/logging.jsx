/*
*	Front-end logging faculties.
*/

class Logger {
	/* The global `log` object is a level-enabled console. */

	constructor(name) {
		this.name = name;
		while (this.name.length < 10) this.name += ' ';

		this.initMS = (new Date()).getTime();
		this.enabled = document.head.getAttribute('data-debug') == 'true';
	}

	log(prefix, color, item) {
		if (!this.enabled) return;

		let time = (((new Date()).getTime() - this.initMS)/1000).toFixed(2) + 's';
		while (time.length < 10) time += ' ';
		while (prefix.length < 10) prefix += ' ';

		console.log('%c' + time + this.name + prefix + item, 'color: ' + color + ';')
	}

	debug(item) {
		/* Log an item at the DEBUG level. */
		this.log('DEBUG', 'gray', item);
		return item;
	}

	info(item) {
		/* Log an item at the INFO level. */
		this.log('INFO', 'black', item);
		return item;
	}

	warning(item) {
		/* Log an item at the WARNING level. */
		this.log('WARNING', 'orange', item);
		return item;
	}

	critical(item) {
		/* Log an item at the CRITICAL level. */
		this.log('CRITICAL', 'red', item);
		return item;
	}
}

@coreComponent
class LogFactory {
	/* A core component for creating logs for a backend-consitant API. */
	
	@exposedMethod
	logger(name) {
		return new Logger(name);
	}
}
