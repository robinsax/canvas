this.Modal = function(){
	/*
		A modal class for extension.
	*/
	this.element = null;

	this.create = function(){
		throw 'Not implemented.'
	}

	this.open = function(){
		this.element = core.page.snap('+div.modal')
			.on('click', this.close)
			.snap('+div.panel')
				.on('click', function(e, evt){
					evt.stopPropagation();
				})
				.snap('+i.fa.fa-times.closer')
					.on('click', this.close)
				.back()
			.back();
		this.create(this.element.snap('div.panel'));
	}

	this.close = function(){
		this.element.remove();
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