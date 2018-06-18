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

		let time = ((new Date()).getTime() - this.initMS)/1000;
		time = (time > 99 ? time.toFixed(0) : time.toFixed(2)) + 's';
		while (time.length < 7) time += ' ';
		while (prefix.length < 6) prefix += ' ';

		let message = '%c' + time + this.name + prefix,
			style = 'color: ' + color + '; background-color: #f0f0f0;';
		if (typeof item == 'string') {
			console.log(message + item, style);
		}
		else {
			console.log(message + ':', style);
			console.log(item);
		}
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
		this.log('WARN', 'orange', item);
		return item;
	}

	critical(item) {
		/* Log an item at the CRITICAL level. */
		this.log('CRIT', 'red', item);
		return item;
	}
}

@coreComponent
class LoggerFactory {
	/* A core component for creating logs for a backend-consitant API. */
	
	@exposedMethod
	logger(name) {
		return new Logger(name);
	}
}
