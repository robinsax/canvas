@coreComponent
class StorageComponent {
	@exposedMethod
	store(key, value) {
		window.localStorage.setItem(key, value);
	}

	@exposedMethod
	stored(key) {
		return window.localStorage.getItem(key);
	}

	@exposedMethod
	unstore(key) {
		let value = window.localStorage.getItem(key);
		window.localStorage.removeItem(key);
		return value;
	}
}