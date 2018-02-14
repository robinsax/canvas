//	Storage.
this.storage = {
	validators: {
		regex: function(repr, val){
			repr = repr.split(':');
			var obj = new RegExp(decodeURIComponent(repr[0]), repr[1] == '1' ? 'i' : ''),
				neg = repr[2] == '1';
			return neg != obj.test(val);
		},
		range: function(repr, val){
			if (val == '' || val == null || val == undefined){
				return false;
			}
			repr = repr.split(',')
			var min = null, max = null;
			if (repr[0] != 'null'){
				min = parseFloat(repr[0]);
			}
			if (repr[1] != 'null'){
				max = parseFloat(repr[1]);
			}
			return (min == null || val >= min) && (max == null || val <= max);
		},
		option: function(repr, val){
			if (repr == 'any'){
				return val != '' && val != null && val != undefined;
			}
		}
	},
	actions: {
		redirect: function(response){
			window.location.href = response.data.url;
		},
		refresh: function(response){
			//	Refresh page, preventing caching.
			var refresh = 1;
			var currentRefresh = self.query['refresh'];
			if (currentRefresh != null){
				refresh = (+currentRefresh) + 1;
			}
			window.location.href = window.location.pathname + '?refresh=' + refresh;
		},
		message: function(response){
			self.flashMessage = response.data.message;
		}
	},
	events: {
		stopPropagation: function(e, evt){
			evt.stopPropagation();
		},
		flashMessage: function(e){
			self.flashMessage = e.attr('cv-message');
		}
	},
	form: null,
	forms: {}
};
