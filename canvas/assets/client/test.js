//	TMP test file.

@cv.view()
class MenuView extends cv.View.define({
	target: '.content',
	live: true,
	data: {
		items: [
			{
				item: 'Fried Rice',
				price: 3.50,
				orders: 0
			},
			{
				item: 'Pizza',
				price: 6.25,
				orders: 0
			}
		],
		orderTotal: 0,
		lastOrdered: null
	},
	template: (data) =>
		<article class="component col-12">
			<h2>Menu</h2>
			<ul>
			{ cv.comp(data.items, (item) =>
				<li class="menu-item">
					{ item.item } - ${ item.price }
					{ item.orders > 0 ? <em> ({ item.orders } orders)</em> : '' }
				</li>
			)}
			</ul>
			<hr/>
			<div id="order-target">
				<i class="fa fa-shopping-cart"></i>
				Place Order!
			</div>
			<ul>
				<li>You've spent ${ '' + data.orderTotal }.</li>
				{ () => {
					if (data.lastOrdered){
						return <li>You last ordered { data.lastOrdered.item }.</li>
					}
				}}
			</ul>
		</article>,
	style: `
		.menu-item {
			padding: 10px 0px; 
		}
		
		#order-target {
			padding: 15px;
			font-size: 20px; 
		}

		#order-target.targeted {
			border: 2px solid red;
		}
	`,
	binding: {
		'.menu-item': (data, el) => {
			cv.drag(el, {
				data: el.data()
			});
		},
		'#order-target': (data, el) => {
			cv.drop(el, {
				accept: (item) => {
					item.orders++;
					data.orderTotal += item.price;
					data.lastOrdered = item;
				}
			})
		}
	}
}){};
