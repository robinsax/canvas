# To-do List Tutorial

## Specification

In this tutorial, we will develop a simple to-do list application which allows users 
to create to-do lists, add items to those lists, and mark items as finished. 

The complete implementation of this application can be found at 

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

To serve canvas locally on port 8080, run

```bash
python3 canvas --serve 8080
```

If you now visit `http://localhost:8080` in your browser, you should see the 'canvas is running' page.

### Defining the Model

Getting your data model right is important, as it is the foundation of your application. Therefore, the first thing we're going to do is define our model of a *to-do list* and a *to-do list item*.

The attributes of a to-do list in our system will be simply a unique ID and the name of its owner. For simplicity, this will be the first name only. We can represent this as a canvas model as follows:

```python
@cv.model('todo_lists', {
	#	The unique identifier. We could alternately use the `uuid` type.
	'id': cv.Column('uuid', primary_key=True),
	#	The name of the owner. Since every list needs an owner, we add a
	#	'not null' constraint to this field. Additionally, we enforce that
	#	names are only one word using a regular expression.
	'owner_name': cv.Column('text', (
		cv.NotNullConstraint(),
		cv.UniquenessConstraint('That name is already taken'),
		cv.RegexConstraint('Must be first name only', r'^[^\s]*$')
	))
})
class TodoList:

	#	A constructor.
	def __init__(self, owner_name):
		self.owner_name = owner_name

	#	A retrieval class method that requires a database session and an
	#	owner name. The purpose of this method may not be clear until we
	#	create our API.
	@classmethod
	def get_or_die(cls, owner_name, session):
		#	Retrieve the instance with the given owner name.
		instance = session.query(cls, cls.owner_name == owner_name, one=True)

		if not instance:
			#	There is no such instance, raise an exception that causes
			#	a 404 Not Found response to be returned to the client
			raise cv.NotFound(owner_name)

		#	Return the instance.
		return instance
```

Next, we want to define what constitutes a to-do list item. A good starting point would be:

* A unique ID.
* A reference to the to-do list to which the item belongs.
* The user-provided text context of the item.
* Whether or not the item is completed.

We could represent this as a canvas model as follows:

```python
@cv.model('todo_list_items', {
	#	Again, a unique identifer.
	'id': cv.Column('uuid', primary_key=True),
	#	A reference to the parent to-do list. Specifically, this field
	#	will contain the value of the `id` of its parent.
	'parent_id': cv.Column('fk:todo_lists.id', (
		cv.NotNullConstraint(),
	)),
	#	The user-provided text content of the item.
	'content': cv.Column('text', (
		cv.NotNullConstraint(),
	)),
	#	Whether or not the item has been completed.
	'finished': cv.Column('bool', default=False)
})
class TodoListItem:

	#	A constructor, which takes a `TodoList` instance and a string
	#	containing the text content of the item.
	def __init__(self, parent, content):
		self.parent_id = parent.id
		self.content = content
```

We now have the two models we need to implement our system.

### Defining an API

There are several methods with which we could provide the functionality of creating and adding items to a to-do list to a *client* (someone or -thing sending requests to our server).

In this tutorial, we will provide an *API*. Generally, this approach is recommended for an innumerable number of reasons.

Our API will consist of the following *endpoint routes* and associated *verbs*:

* The list endpoint: `/api/list/<owner_name>`
	* `get`: Retrieve the to-do list of this name and its contained items.
	* `put`: Create a new to-do list for this name.
* The list item endpoint: `/api/item/<owner_name>`
	* `put`: Add an item to the to-do list of this owner.

#### The List Endpoint

We can translate our specification for the *list endpoint* into a canvas controller as follows:

```python
#	Define and register our endpoint class as being responsible for
#	the decided route. This route contains a variable (owner_name), which
#	we will access when handling requests.
@cv.endpoint('/api/list/<owner_name>')
class ListEndpoint:

	#	This method is invoked to handle the `get` verb. It is responsible
	#	for returning the to-do list whose owners name is `owner_name`, or
	#	returning a 404 Not Found HTTP code if no such list exists.
	def on_get(self, context):
		#	Alias the database session.
		session = context.session

		#	Retrieve the to-do list for this owner using the class method
		#	we defined earlier. Note that it handles the case where no
		#	such to-do list exists (hence the 'or_die').
		todo_list = TodoList.get_or_die(context.route.owner_name, session)

		#	Retrieve all items belonging to this to-do list.
		items = session.query(TodoListItem, TodoListItem.parent_id == todo_list.id)
		
		#	Create a dictionary containing representing our to-do list.
		dictized = cv.dictize(todo_list)
		#	Add an attribute containing the *dictizations* of the items.
		dictized['items'] = cv.dictize(items)

		#	Return a JSON response containing the to-do list and its items
		# 	to the client.
		return cv.create_json('success', dictized)

	#	This method is invoked to handle the `put` verb. It is responsible
	#	for creating a new to-do list.
	def on_put(self, context):
		#	Read the name of the owner.
		owner_name = context.route.owner_name

		#	Create a `TodoList` object with the given owner.
		todo_list = TodoList(owner_name)

		#	Save the new instance in the database and commit the
		#	transaction.
		context.session.save(todo_list).commit()

		#	Inform the client the operation was successful.
		return cv.create_json('success')
```

#### The Item Endpoint

We can translate our specification for the *list item endpoint* into a canvas controller as follows:

```python
@cv.endpoint('/api/item/<owner_name>')
class ListItemEndpoint:

	#	This method is invoked to handle the `put` verb. It is responsible
	#	for asserting that a to-do list for owner_name exists and adding
	#	a new item as described in the request body to it if so.
	def on_put(self, context):
		#	Alias the database session.
		session = context.session

		#	As before, retrieve the to-do list for this owner.
		parent_todo_list = TodoList.get_or_die(context.route.owner_name, session)
		
		#	Create our new to-do list item. Reading from `context.request`
		#	implicitly requires the client to have provided whatever
		#	values we read in the request body, which by default is JSON.
		item = TodoListItem(parent_todo_list, context.request.content)

		#	Use the database session to save our new item and commit the
		#	transaction.
		session.save(item).commit()
	
		#	Inform the client the operation was successful.
		return cv.create_json('success')
```

###	Creating the Interface

Now we have an to-do list model, and an API that allows us to control it. At this point you should try creating a to-do list, adding an item to it, and retrieving it using `curl`, the `requests` library for Python, or a similar method.

The final step is to provide a web page with an interface that allows users to control their
to-do list from their browser.

There are three aspects to this:

* Defining a controller to serve the page.
* Defining a Jinja template of the static part of that page.
* Defining a to-do list `View` and an owner name entry `Form` in Javascript and placing them on the page.

The use case for this interface is:

1. The user visits the page.
1. They enter their name in a field.
1. If the name they provide is not associated with an existing to-do list, they are asked if they want to create one.
1. They are presented with an interactive view of their to-do list.

#### The Page Controller

Notice how we registered our API's controllers using the `endpoint` decorator. This informed canvas that we were creating... well, endpoints. Similarly, we can use the `page` decorator on a controller class to inform canvas we are creating a page.

Lets say our to-do list interface will live at the route `/todo`, and its HTML template at `./assets/templates/todo.html` in our plugin's folder. Our page controller could then be defined with simply:

```python
@cv.page('/todo')
class TodoPage: pass
```

We are going to make one addition. Our page is going to contain a small form with which users will supply their name. Therefore it will contain a field modeled after the `owner_name` attribute of our `TodoList` model. canvas provides a method for easily generating forms based off of models. To use it, we tell canvas to include a *serialization* of our model with our page so our form-generation JavaScript can reference it. This is done by adding a `models` option to the `page` decorator, like so:

```python
@cv.page('/todo', models=(TodoList,))
class TodoPage: pass
```

When we create our form, we can now reference the fact that it is based on `'todo_lists'` (the name we gave our `TodoList` model). This will be explained further when we make use of it; for now, just understand that we are providing a representation of our `TodoList` model to our frontend.

#### The Template

Every page needs a Jinja *HTML template*. If the concept of HTML templating is unfamiliar, check out Jinjas' documentation.

In this case, we can use the following template:

```html
{# Inform canvas's template loader that this template extends the base page template. #}
{% page %}

{# Set the title of the page. #}
{% set title = 'To-do List Manager' %}

{# Add the JavaScript file which will contain our view as a dependency. #}
{% set dependencies = ['todo_list.js'] %}

{# Define the contents of the 'page' section of the document (as opposed to the header, footer, etc.). #}
{% block page %}
	{# Note: See features/page_layout.md for an explanation of the 'component col-12' class. #}
	<div class="component col-12"/>
		{# Inform the front end we want a form called 'owner' (which we'll define presently) to be placed here. #}
		<cv-form cv-name="ownerName"></cv-form>
	</div>
	<div class="component col-12"/>
		{# Inform the front end we want a view called 'todoList' (which we'll define presently) to be placed here. #}
		<cv-view cv-name="todoList"></cv-view>
	</div>
{% endblock %}
```

This file should live at `./assets/templates/todo.html`.

#### The JavaScript

Now we need to create our JSX file, `todo_list.jsx`, where we will define our to-do list view. Note that in our page template, we referred to this file with a `.js` extension. This is because canvas will recognize requests for non-existant `.js` files as potentially referencing a `.jsx` file, and will compile and serve the latter in its place. The same is true of `.less` and `.css`.

This file should live as `./assets/client/todo_list.jsx` in our plugin folder.

The syntax used to define a view or form in canvas is similar to that of a model or controller (that is, decorator based).

#### The View 

Views are used to render data as HTML. They have 3 primary components:

* `data`, an attribute containing the data they represent.
* `state`, an attribute containing an arbitrary object describing their state.
* a `template` function, which maps `data` and `state` to an HTML representation.

We want to define our to-do list view such that, given a owner name, it:

* Collects their to-do list from the `/api/list/<owner_name>` endpoint we created earlier.
* Displays it, and provides the ability to add items.

The view will be provided the name of the to-do list owner from our form.

The following code defines our view.

```javascript
//	Register our view as being called 'todoList'.
@cv.view('todoList', {
	//	The state of this view consists of only its owner name.
	state: {ownerName: null},
	//	Our JSX template.
	template: (data, state) => 
		!data.items ? () => {} : 	//	If there is no data, don't render anything.
		<div class="todo-list component col-12">
			<h1>{ state.ownerName }'s To-do List</h1>
			<ul>
				{ tk.comp(data.items, item => <li>{ item.content }</li>) }
			</ul>
			<input type="text" placeholder="Add an item..."/>
			<button>Add</button>
		</div>
})
class TodoListView {
	//	This method sets the owner name and fetches their to-do list.
	setOwnerName(ownerName) {
		this.state.ownerName = ownerName;
		this.dataSource = '/api/list/' + ownerName;
		this.fetch();
	}

	//	This method is triggered by the button being clicked. It adds
	//	an item to the to-do list by sending a request to the 'add item'
	//	endpoint we created, then re-fetching its data.
	@cv.event('button')
	addItem() {
		//	Read the input value.
		let content = tk('input').value();

		//	Send a request to the 'add item' endpoint, with a request
		//	body containing the item content (compare this with how we
		//	are reading the request body at that endpoint).
		cv.request('put', '/api/item/' + this.state.ownerName)
			.json({content: content})
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

Like views, forms use template to create an HTML representation of themselves. However, they don't have a `data` attribute. Instead, their template is passed a variable called `fields`, which can be "printed" directly.

The form decorator should also be passed a definition of its fields. In this case, we supplied a model which we can use to do the majority of form definition.

In this case, our form should:

1. Have a single field, with which the user can input their name.
1. Ensure a to-do list exists for that user, and if not give them the option to create one.
1. Pass the username to the view we defined by calling its `setOwnerName()` method.

The following code defines our form.

```javascript
//	Define the form as being named 'ownerName'.
@cv.form('ownerName', {	
	//	State that this form is based on the to-do list model.
	model: 'todo_lists',
	//	Declare the list fields we want to include in this form.
	fields: [
		//	This list can contain strings or string, object pairs.
		//	In the latter case, the object is used to override default values.
		['owner_name', {
			label: 'Your Name',
			placeholder: 'e.g. Jane'
		}]
	],
	//	Our state simple contains a flag that decides whether or not this
	//	form renders.
	state: {closed: false},
	//	The template checks whether it should render, then provides a simple wrapper
	//	around its fields.
	template: (fields, state) =>
		state.closed ? () => {} :
		<div class="form">
			<h1>To-do List Manager</h1>
			<p>Please enter your name to continue...</p>
			{ fields }
			<button>Enter</button>
		</div>
})
class OwnerNameForm {
	getOwnerName() {
		//	Return the value of the owner_name field.
		return this.fields.owner_name.value();
	}

	openView() {
		//	Open the 'todoList' view for the current owner.
		cv.views.todoList.setOwnerName(this.getOwnerName());
		this.state.closed = true;	
	}

	@cv.event('button')
	submit() {
		//	Our form submission function, triggered when the button is clicked.

		//	Compute the URL of the list endpoint for this owner.
		let endpointURL = '/api/list/' + this.getOwnerName();

		//	Check if the to-do list exists, and create it if it doesn't.
		cv.request('get', endpointURL)
			.success(() => this.openView())
			.failure(() => {
				cv.request('put', endpointURL)
					.success(() => {
						this.openView();
					})
					.send();
			})
			.send();
	}
}
```

Done! Run the following to serve the application.

#	TODO: Mark as complete.