//	::import ui, api
//	::style someStyle
//	::export doThing

const doThing = () => {
	ui.createAlert(api.get('/current_alert'));
}
