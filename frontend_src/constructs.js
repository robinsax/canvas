this.Modal = function(){
	/*
		A modal class for extension.
	*/
	var self = this;
	this.element = null;

	this.create = function(){
		throw 'Not implemented.'
	}

	this.open = function(){
		this.element = tk.page.snap('+div.modal')
			.on('click', this.close)
			.snap('+div.panel')
				.on('click', function(e, evt){
					evt.stopPropagation();
				})
				.snap('+i.fa.fa-times.closer')
					.on('click', this.close)
				.back()
			.back();
	}

	this.close = function(){
		self.element.remove();
	}
}

this.modal = function(modalClass){
	/*
		Create, open, and return an instance of the given Modal class.
	*/
	var inst = new modalClass();
	inst.open();
	return inst;
}