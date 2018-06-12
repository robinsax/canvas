@part
class StoragePart {
	constructor() {
		core.store = this.store.bind(this);
		core.unstore = this.unstore.bind(this);
	}

	store(key, value) {
		window.localStorage.setItem(key, value);
	}

	unstore(key, hard=false) {
		let value = window.localStorage.getItem(key);
		if (hard) {
			window.localStorage.removeItem(key);
		}
		return value;
	}
}
