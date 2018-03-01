this.dnd = function(element, data){
	this.dnd.end();
	element.on('mousedown', function(e, event){
		self.dnd.currentElement = core.page.append(element.copy().classify('dnd-dragging'));
		self.dnd.currentData = data;
		event.preventDefault();
	});
}
this.dnd.currentElement = null;
this.dnd.currentData = null;
this.dnd.target = function(element, func){
	var acceptFunc = tk.varg(arguments, 2, tk.fn.tautology);
	element.on({
		mouseover: function(e){
			if (self.dnd.currentData != null){
				e.classify('dnd-targeted');
			}
		},
		mouseout: function(e){
			e.classify('dnd-targeted', false);
		},
		mouseup: function(e){
			if (self.dnd.currentData == null){
				return;
			}
			if (acceptFunc(self.dnd.currentData)){
				func(self.dnd.currentData);
			}
			else {
				self.flashMessage = 'Can\'t drop that there';
			}
		}
	});
}
this.dnd.end = function(){
	if (self.dnd.currentElement != null){
		self.dnd.currentElement.remove();
		self.dnd.currentElement = self.dnd.currentData = null;
	}
}

tk.init(function(){
	tk('body > .page').on({
		mouseup: function(){
			self.dnd.end();
		},
		mousemove: function(e, event){
			if (self.dnd.currentElement != null){
				self.dnd.currentElement.css({
					top: event.clientY,
					left: event.clientX
				});
			}
		}
	})
});