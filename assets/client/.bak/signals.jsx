@part
class SignalsPart {
	constructor() {
		this.map = {};

		core.receives = this.receives.bind(this);
		core.signal = this.signal.bind(this);
	}

	receives(signalName) {
		return (target, key) => {
			this.map[signalName] = this.map[signalName] || [];
			this.map[signalName].push([target, key]);
		}
	}

	signal(signalName, data=null) {
		tk.iter(this.map[signalName] || [], parts => {
			let prototype = parts[0], key = parts[1];
			tk.iter(prototype.constructor._instances, instance => {
				instance[key](data);
			})
		});
	}
}