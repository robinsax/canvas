@cv.controller('/routes')
class MyPageController {
	constructor() {
		this.view = new cv.View({
			template: (item) => {
				<div class="item">{ item }</div>
			},
			dataSource: () => {
				cv.request().json({action: 'get_data'})
			}
		});

		this.thing = 0;
	}

	init() {
		this.view.render();
	}

	@cv.action
	updateThing() {
		this.thing += 1;
	}
}