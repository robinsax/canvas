@coreComponent
class StorageComponent {
	@exposedMethod
	store(key, value) {
		window.localStorage.setItem(key, JSON.stringify(value));
	}

	@exposedMethod
	stored(key) {
		return JSON.parse(window.localStorage.getItem(key));
	}

	@exposedMethod
	unstore(key) {
		let value = this.stored();
		window.localStorage.removeItem(key);
		return value;
	}
}