# To-do List Tutorial

## Specification

In this tutorial, we will develop a simple to-do list application which allows users 
to create to-do lists, add items to those lists, and mark items as finished. 

The complete implementation of this application can be found in its [repository](https://github.com/robinsax/cvpl-todo.git).

## Building It!

*Note*: If you have not yet installed canvas, see `installing.md`.

### Creating a Plugin

canvas web applications are implemented as a set of one or more plugins. To create our to-do list, we first need to create a plugin. We'll call it `todo`.

Running the following will create our to-do plugin in our plugins folder, which by default lives at `../canvas_plugins` (relative to canvas itself), and activate it.

```bash
python3 canvas --create-plugin todo --config "plugins.activated=todo,"
```

When should now have a folder called `cvpl-todo`, which contains some configuration files and the folders `assets`, `tests`, and `todo`. The latter is the Python package from which canvas will load our plugin.

### Sanity Check

To ensure everything is set up correctly, let's serve canvas and make sure the 'Welcome' page is available.

To serve canvas locally on port 80, run

```bash
python3 canvas --serve 80
```

If you now visit `http://localhost` in your browser, you should see the default welcome page.

### Defining the Model

Getting a data model right is important as it's is the foundation of your application. Therefore, 
the first thing we're going to do is define our model of a *to-do list* and a *to-do item*.

The attributes of a to-do list in our system will be simply a unique ID and its name. 
We can represent this as a canvas model as follows:

```python
#	Our to-do list model will be stored in a table called 'todo_lists'.
@cv.model('todo_lists', {
	#	It has UUID 'id' as a primary key...
	'id': cv.Column('uuid', primary_key=True),
	#	..and a required name.
	'name': cv.Column('text', (
		cv.NotNullConstraint(),
	))
#	When we 'dictize' (i.e. serialize into a dictionary) a to-do list,
#	we want to include it's items. We define that property below.
}, dictized=('items',))
class TodoList:

	#	To create a to-do list all we need to know is the name.
	def __init__(self, name):
		self.name = name

	#	The cached_property() decorator is an extension of Python's
	#	builtin property() decorator. It caches the value of the
	#	property. In this case, that prevents multiple identical
	#	database queries.
	@cv.cached_property 
	def items(self):
		#	Using the session that loaded this model, query its items.
		return self.__session__.query(TodoItem, TodoItem.parent_id == self.id, order_by=TodoItem.content)
```

Next, we want to define what constitutes a to-do item. A good starting point would be:

* A unique ID.
* A reference to the to-do list to which the item belongs.
* The user-provided textual context of the item.
* Whether or not the item is completed.

We could represent this as a canvas model as follows:

```python
#	Our to-do list item model will be stored in a table called
#	'todo_list_items'.
@cv.model('todo_items', {
	#	It has UUID 'id' as a primary key...
	'id': cv.Column('uuid', primary_key=True),
	#	...a reference to its containing list...
	'parent_id': cv.Column('fk:todo_lists.id', (
		cv.NotNullConstraint(),
	)), 
	#	...textual content...
	'content': cv.Column('text', (
		cv.NotNullConstraint(),
	)),
	#	...and wether or not it is marked as finished.
	'finished': cv.Column('bool', default=False)
})
class TodoItem:

	#	To create a to-do list item, we need to know its parent
	#	list and it's textual content.
	def __init__(self, parent, content):
		self.parent_id = parent.id
		self.content = content
```

We now have the two models we need to implement our system.

### Defining an API

There are several methods with which we could provide the functionality of creating, adding, and modifying 
these items to a to-do list to a *client* (someone or -thing sending requests to our server).

In this tutorial, we will provide a JSON *API*. Generally, this approach is recommended for an innumerable 
number of reasons.

Our API will consist of the following *endpoint routes* and associated *verbs*:

* The list endpoint: `/api/lists`
	* `get`: Retrieve all to-do lists.
	* `put`: Create a new to-do list given a name.
* The item endpoint: `/api/items`
	* `put`: Create a new to-do list item given the ID of the parent list and some textual content.
	* `patch`: Toggle the finished state of a to-do item given its ID.

#### The List Endpoint

We can translate our specification for the *list endpoint* into a canvas controller as follows:

```python
#	Our list endpoint will live at '/api/lists'.
@cv.endpoint('/api/lists')
class ListEndpoint:

	#	This method handles 'get' requests. It returns all to-do lists.
	def on_get(self, context):
		#	Read all to-do lists our of our database.
		lists = context.session.query(TodoList)

		#	Serve a canonical JSON response containing a list of to-do 
		#	list dictizations in its data package.
		return cv.create_json('success', cv.dictize(lists))

	#	This method handles 'put' requests. It creates a new to-do list
	#	given a name.
	def on_put(self, context):
		#	This shorthand allows easier access to the most commonly
		#	used contents of the request context.
		request, cookie, session = context[:3]

		#	Create a new TodoList given the name supplied in the
		#	request JSON.
		new_list = TodoList(request.name)

		#	Write the list to the database and commit our changes.
		session.save(new_list).commit()

		#	Serve a canonical JSON response.
		return cv.create_json('success')
```

#### The Item Endpoint

We can translate our specification for the *item endpoint* into a canvas controller as follows:

```python
#	Our item endpoint will live at '/api/items'.
@cv.endpoint('/api/items')
class ListItemEndpoint:

	#	This method handles 'put' requests. It creates a new item given
	#	a parent list and some textual content.
	def on_put(self, context):
		#	Unpack the request context.
		request, cookie, session = context[:3]

		#	Retrieve the parent to-do list specified in the request context.
		parent = TodoList.get(request.parent_id, session)

		if not parent:
			#	If there is no such parent to-do list, we cannot process the
			#	request (this exception results in a 422 HTTP status code).
			raise cv.UnprocessableEntity('No list with ID %s'%request.parent_id)
		
		#	Create a new item.
		item = TodoItem(parent, request.content)

		#	Write the item to our database and commit the changes.
		session.save(item).commit()

		#	Serve a canonical JSON response.
		return cv.create_json('success')

	#	This method handles 'patch' requests. It marks an item as finished
	#	given its ID.
	def on_patch(self, context):
		#	Unpack the request context.
		request, cookie, session = context[:3]

		#	Retrieve the item specified in the request.
		item = TodoItem.get(request.item_id, session)
		if not item:
			#	If there is no such item we cannot process the request.
			raise cv.UnprocessableEntity('No item with ID %s'%request.item_id)

		#	Toggle the item's finished attributel.
		item.finished = not item.finished

		#	Save our changes.
		session.commit()

		#	Serve a canonical JSON response.
		return cv.create_json('success')
```

###	Creating the Interface

Now we have an to-do list model, and an API that allows us to control it. At this point you should try 
creating a to-do list, adding an item to it, and retrieving it using `curl`, the `requests` library for 
Python, or a similar method.

The final step is to provide a web page with an interface that allows users to control to-do lists 
from their browser.

There are four aspects to this:

* Defining a controller to serve the page.
* Defining a Jinja template of the static part of that page.
* Defining a to-do list `View` and and list creation `Form` in Javascript and placing them on the page.
* Authoring a LESS stylesheet.

#### The Page Controller

Notice how we registered our API's controllers using the `endpoint` decorator. This informed canvas 
that we were creating... well, endpoints. Similarly, we can use the `page` decorator on a controller class to 
inform canvas we are creating a page.

Lets say our to-do list interface will live at the domain root, and its HTML template at 
`./assets/templates/todo.html` in our plugin's folder. Our page controller could then be defined with:

```python

#	The page on which our interface will live will be the root of our domain
#	(e.g. http://localhost/). It's Jinja template is 'todo.html'. Finally,
#	we want to include a representation of our TodoList model with which we
#	can create a form for adding to-do lists.
@cv.page('/', template='todo.html', models=(TodoList,))
class TodoPage:
	#	We don't need anything here; the default behaviour of a page is to
	#	render and serve it's template on 'get', which is what we want.
	pass

```

#### The Template

Every page needs a Jinja *HTML template*. If the concept of HTML templating is unfamiliar, check out Jinjas' documentation.

In this case, we can use the following template:

```html
{# Inform canvas's template loader that this template extends the base page template. #}
{% page %}

{# Set the title of the page. #}
{% set title = 'To-do List Manager' %}

{# Add our JavaScript and CSS as dependencies. #}
{% set dependencies = ['todo_list.js', 'todo_list.css'] %}

{# Define the contents of the 'page' section of the document (as opposed to the header, footer, etc.). #}
{% block page %}
	{# Place and name our list view and form. #}
	<x-TodoListView data-name="lists"></x-TodoListView>
	<x-TodoListForm data-name="list"></x-TodoListForm>
{% endblock %}
```

This file should live at `./assets/templates/todo.html`.

#### The JavaScript

Now we need to create our JSX file, `todo_list.jsx`, where we will define our to-do list view. Note that 
in our page template, we referred to this file with a `.js` extension. This is because canvas will 
recognize requests for non-existant `.js` files as potentially referencing a `.jsx` file, and will compile 
and serve the latter in its place. As we will see later, the same is true of `.less` and `.css`.

This file should live as `./assets/client/todo_list.jsx` in our plugin folder.

The syntax used to define a view or form in canvas is similar to that of a model or controller (that is, decorator based).

#### The View 

Views are used to render data as HTML. They have 3 primary components:

* `data`, an attribute containing the data they represent.
* `state`, an attribute containing an arbitrary object describing their state.
* A `template` function, which maps `data` and `state` to an HTML representation.

We want to define our to-do list view such that it:

* Displays all to-do lists.
* Displays the items of the current to-do list, including a button to mark them as finished.

The following code defines our view.

```javascript
/*
	This view consists of two components:
	* A list of all to-do lists with a button to open the creation form.
	* The title and contents of the currently selected to-do list, where
	  each item includes an icon that can be clicked to mark it as finished.
*/
@cv.view({
	//	The data for this view is retrieved from our list endpoint.
	dataSource: '/api/lists',
	//	The state of this view contains the index of the currently
	//	selected list.
	state: {currentI: -1},
	//	Since our template is somewhat complex, we split it up by specifying
	//	a 'templates' object instead of just a 'template'. The 'root' entry
	//	is the base.
	templates: {
		//	This renders our list of to-do lists, or a hint if there aren't 
		//	any yet.
		lists: (data, state) =>
			<div class="lists">
				{ data.length > 0 ?
					//	If there are any lists, render them, marking the 
					//	current one with the 'current' class so we can
					//	style it differently.
					tk.comp(data, (list, i) =>
						<div class={ "tile" + (state.currentI == i ? " current" : "") }>
							<h3>{ list.name }</h3>
							<aside class="subtext">{ list.items.length + '' } items</aside>
						</div>
					)
					:
					//	If there are no lists, render a hint.
					<p class="subtext">Create a list</p>
				}
			</div>,
		//	This renders our currently selected to-do list.
		currentList: (currentList) =>
			<div>
				<h2>{ currentList.name }</h2>
				<ul>
					{ 
					//	Render the items and their finished buttons, 
					//	marking the finished ones with the 'finished' class.
					  tk.comp(currentList.items, item => 
						<li class={ item.finished ? "finished" : "" }>{ item.content } <i class="fa fa-check mark-done"/></li>
					)}
				</ul>
				{ 
				//	Provide an input and associated button for adding new
				//	items.
				}
				<input type="text" name="new_item" placeholder="Add an item..."/>
				<button class="add-item">Add</button>
			</div>,
		//	This is the base template. Its third parameter, 'templates', is
		//	the set of our defined templates.
		root: (data, state, templates) =>
			<div class="todo-list">
				<h1 class="align-center">To-do Lists</h1>
				<div class="component col-6">
					{ 
					//	Render our 'lists' template defined above, and a button
					//	for adding new lists.
					templates.lists(data, state) 
					}
					<div class="padding">
						<button class="add-list">Add a List</button>
					</div>
				</div>
				<div class="component col-6">
					{ 
					//	Either render the current list or a hint if there is no
					//	current list.
					state.currentI >= 0 ?
						templates.currentList(data[state.currentI])
						:
						<p class="subtext">Select a list</p>
					}
				</div>
			</div>
	}
})
class TodoListView {
	//	Bind an event to to-do list tiles that sets the current list
	//	in state.
	@cv.event('.tile')
	setCurrent(el) {
		//	ToolkitSelection.index() returns the index of the element in 
		//	its source comprehension.
		this.state.currentI = el.index();
	}

	//	Bind an event to our add list button that opens the to-do list
	//	form.
	@cv.event('.add-list')
	openListForm() {
		cv.forms.list.open();
	}

	//	Bind an event to the icon in each to-do item that marks it as 
	//	finished.
	@cv.event('.mark-done')
	markDone(el) {
		//	Send a patch request to our items endpoint, then refresh
		//	our view.
		cv.request('patch', '/api/items')
			.json({
				item_id: el.data().id
			})
			.success(() => {
				this.fetch();
			})
			.send();
	}

	//	Bind an event to our add item button that adds a new item.
	@cv.event('.add-item')
	addItem() {
		//	Retrieve our input.
		let input = tk('input[name="new_item"]'),
		//	Read it's value.
			content = input.value();

		//	If it has no value, return.
		if (!content) { return; }
		
		//	Clear it.
		input.value('');
		
		//	Send a put request to our items endpoint to create a new
		//	item, then refresh our view.
		cv.request('put', '/api/items')
			.json({
				parent_id: this.data[this.state.currentI].id,
				content: content
			})
			.success(() => {
				//	The operation was successful, refresh the list.
				this.fetch();
			})
			.send();
	}
}
```

#### The Form

canvas abstracts forms.

Like views, forms use template to create an HTML representation of themselves. However, they don't 
have a `data` attribute. Instead, their template is passed a variable called `fields`, which can be "printed" directly.

The form decorator should also be passed a definition of its fields. In this case, we supplied a model 
which we can use to do the majority of form definition.

The following code defines our form.

```javascript
/*
	A to-do list creation form that opens in a modal.
*/
@cv.form({
	//	This form is based on our TodoList model.
	model: 'TodoList',
	//	It is submitted via HTTP put to /api/lists
	target: '/api/lists',
	method: 'put',
	//	It contains a single field, the 'name' attribute of our
	//	model. We override a single default value, the placeholder.
	fields: [
		['name', {
			placeholder: 'e.g. My To-do List'
		}]
	],
	//	The template is simply a wrapper around the fields.
	template: fields =>
		<div class="form">
			<h2>Add a List</h2>
			{ fields }
			<button>Add</button>
		</div>
})
class TodoListForm extends cv.ModalForm {
	//	When a new list is successfully created, referesh the list 
	//	view (so the new list is added).
	@cv.onSuccess
	fetchView() {
		cv.views.lists.fetch();
	}

	//	Bind submission to the button in our template.
	@cv.event('button')
	submit() {
		super.submit();
	}
}
```

#### The Stylesheet

We included a stylesheet called `todo_list.css` in the dependencies of our template,
but we want to user LESS to author it. Therefore, this file must live at 
`./assets/client/todo_list.less`.

The following adds some simple styling to our page.

```less
//	Since canvas includes a base stylesheet, plugin styles are generally
//	contained in a body selector to allow them to override the base easily.
body {
	//	We want our tiles, which represent lists, to be inline block.
	.tile {
		display: inline-block;
		vertical-align: top;
		margin: 20px;
		padding: 10px;
		cursor: pointer;

		&.current {
			//	Highlight the currently selected list.
			background-color: @theme1;
		}
	}

	li {
		i {
			//	The 'mark finished' icons will float to the right and
			//	be red by default.
			float: right;
			color: @error;
			cursor: pointer;
		}

		&.finished {
			//	Strike out completed items, and set their icon color
			//	to green.
			text-decoration: line-through;

			i {
				//	Change the color of the 'mark finished' icon to
				//	green if the item is completed.
				color: @success;
			}
		}
	}
}
```

Done! Run the following (with CWD as the canvas directory) to serve the application.

```
python canvas --serve 80
```
