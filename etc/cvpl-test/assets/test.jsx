@cv.view({
	state: {
		itemClass: null,
		controlClass: null,
		properList: false,
		count: -1,
		offset: 0,
		filter: x => x
	},
	subtemplates: {
		item: item => <div class="item">{ JSON.stringify(item) }</div>,
		listContent: (data, state, subtemplates) => data.length == 0 ? 
			<p class="subtext">Nothing to show</p>
			:
			cv.comp(state.filter(data), (item => 
				state.itemClass ? new state.itemClass(item) : subtemplates.item 
			), state.offset, state.offset + state.count)
	},
	template: (data, state, subtemplates) =>
		<div class="list">
			{ state.controlClass ? new state.controlClass() : <span/> }
			{ state.properList ? 
				<ul class="items">
					{ subtemplates.listContent(data, state, subtemplates) }
				</ul>
				:
				<div class="items">
					{ subtemplates.listContent(data, state, subtemplates) }
				</div>	
			}
		</div>
})
class ListView {
	attachToParent(parent) { parent.list = this; }
	
	onceConstructed(options) {
		this.data = options.data;
		this.state.itemClass = options.itemClass || null;
		this.state.count = options.count || -1;
		this.state.properList = options.properList || false;
		this.state.controlClass = options.controlClass || null;

		this.itemStates = {};
	}

	update(stateUpdates) {
		this.state.update(stateUpdates);
	}

	get length() {
		return this.state.filter(this.data).length;
	}
}

@cv.view({
	state: {
		pageLength: -1,
		currentPage: 0,
		pageCount: 1,
		search: null
	},
	template: state =>
		<div class="align-right controls">
			<button class="refresh">Refresh</button>
			<label>Page Length: </label><input class="page-length" type="number" value="-1"/><br/>
			<label>Search: </label><input class="search" type="text"/>
			<div class="subtext">
				<button class={ "prev" + (state.currentPage == 0 ? " invisible" : "") }>Previous</button>
				<button class={ "next" + (state.currentPage == state.pageCount - 1 ? " invisible" : "") }>Next</button>
				{ state.currentPage + 1} / { state.pageCount }
			</div>
		</div>
})
class CustomListControls {
	attachToParent(parent) { parent.controls = this; }

	@cv.event('.refresh')
	refreshList() {
		this.parent.fetch();
	}

	updateState(update) {
		this.state.update(update);
		this.parent.update({
			count: this.state.pageLength,
			offset: this.state.pageLength*this.state.currentPage,
			filter: this.state.search === null ? x => x : (search =>
				items => cv.comp(items, item => item.text.indexOf(search) >= 0 ? item : undefined)
			)(this.state.search)
		});
		this.state.pageCount = Math.max(1, Math.ceil(this.parent.length / this.state.pageLength));
	}

	@cv.event('.next')
	next() {
		this.updateState({
			currentPage: this.state.currentPage + 1
		});
	}

	@cv.event('.prev')
	prev() {
		this.updateState({
			currentPage: this.state.currentPage - 1
		});
	}

	@cv.event('.page-length', 'change')
	updatePageLength(context) {
		this.updateState({
			pageLength: +context.element.value
		});
	}

	@cv.event('.search', 'change')
	@cv.event('.search', 'keyup')
	updateSearch(context) {
		this.updateState({
			search: context.element.value
		});
	}
}

@cv.view({
	state: {
		clicked: null, 
		hovered: false
	},
	template: (item, state) => 
		<li class={ "item" + (state.clicked ? " highlight" : "") + (state.hovered ? " success" : "") }>
			<strong>{ item.text } </strong>
			<em>({ item.number })</em>
			<ol>
				{ cv.comp(item.kids, k => <li>{ k }</li>) }
			</ol>
		</li>
})
class CustomItemView {
	constructor() {
		this.x = false;
	}

	onceConstructed(item) {
		this.data = item;
	}

	beforeDestroyed() {
		if (this.state.clicked === null) return;
		this.parent.itemStates[this.data.text] = this.state.bind(() => {}).observe();
	}

	onceCreated() {
		this.x = true;
		let state = this.parent.itemStates[this.data.text];
		if (state) {
			this.state = state.bind(this.render.bind(this)).observe();
		}
		
		this.render();
	}

	@cv.event('.item')
	click() {
		this.state.clicked = !this.state.clicked;
	}

	@cv.event('.item', 'mouseover')
	hover() {
		this.state.hovered = true;
	}

	@cv.event('.item', 'mouseout')
	unhover() {
		this.state.hovered = false;
	}

	hasChanged(other) { return true; }
}

@cv.page('/test')
@cv.view({
	template: () =>
		<div class="align-center">
			<div class="col-6 align-left">
				<h3>Test components</h3>
				{ new ListView({
					data: cv.dataCache('/api/trash'),
					properList: true,
					controlClass: CustomListControls,
					itemClass: CustomItemView
				}) }
			</div>
		</div>
})
class TestView {
	onceCreated() {
		window.t = this;
		//setInterval(() => cv.fetch('/api/trash'), 5000);
	}
}