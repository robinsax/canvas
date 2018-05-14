@part
class StoragePart {
	constructor() {
		core.store = this.store.bind(this);
		core.unstore = this.unstore.bind(this);
	}

	store(key, value) {
		window.localStorage.setItem(key, value);
	}

	unstore(key) {
		return window.localStorage.getItem(key);
	}
}
