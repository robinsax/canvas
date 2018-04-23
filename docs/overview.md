# Overview of canvas

canvas is a web application framework written in Python and Javascript (more specifially, JSX). It is losely based on the model-view-controller pattern.

It aims to provide a modern toolchain and boilerplate free interface that
allows complex systems to be developed in a comprehensible, extensible way.

This document is not a tutorial, it simply gives an overview of some of the primary components that comprise a canvas application.

## Backend

### Models

Models are persistant storage. They are exposed as Python objects that are mapped to a row in a database. A *model class* is analogous to a database table, and a *model instance* of that class is analogous to a row in that table.

This object-relational mapping is managed by a *session* object, which can be used to read, create, modify, and delete rows in a table with operations on model classes and instances.

The following code sample uses canvas's `model()` decorator to define a model class representing a simple implementation of a 'user'.

```python
import canvas as cv

@cv.model('users', {
	'id': cv.Column('serial', primary_key=True),
	'api_key': cv.Column('uuid'(
		cv.NotNullConstraint(),
	)),
	'name': cv.Column('text', (
		cv.NotNullConstraint(),
	)),
	'email': cv.Column('text', (
		cv.NotNullConstraint(),
		cv.RegexConstraint('Invalid email format', r'[\w\.]+@\w+(?:.\w+)+')
	))
})
class User: pass
```

This declaration causes canvas to create a table in Postgres for storing instances of this model, and allow sessions to accept its, or joins containing it, as a target on which to perform database operations.

The following code sample uses a session to print out the username and email of all existing users.

```python
import canvas as cv

session = cv.create_session()

for user in session.query(User):
	print('Username: %s, Email: %s'%(user.name, user.email))
```

### Controllers

Controllers are singleton objects responsible for handling requests to one or more given *routes* (a.k.a. paths). They are implemented by defining classes and registering them via decorator.

To handle requests, controllers may implement one or more methods of the form `on_get()`, `on_post()`, `on_put()`, etc. These methods take a single parameter besides `self`; a *request context*. The request context contains, believe it or not, the *context* of the request, including its supplied parameters, cookie session, and a database session with which to read and write data.

The following code sample defines a simple controller which greets a client, given that they have provided their name in the *query string*.

For example, a `get` request to `/greet?name=Jane` will receive the response `'Hello Jane'`.

```python
import canvas as cv

@cv.controller('/greets')
class GreetController:

	def on_get(self, context):
		if 'name' not in context.request:
			return 'Please provide your name'
		return 'Hello %s'%context.request.name
```

## Frontend

### Views

Views are written in JSX, which is a super-set of ES6 that includes HTML syntax. They have `data` and a `state`, which are used to produce markup via a *template*.

Views allow the DOM to be expressed as a function of data, solving the quintessential issue of keeping the two synchronized.

The following code sample defines a view which displays a list of words. It makes use of the *list comprehension* functionality of `toolkit.js`, the DOM manipulation and general helper library used by canvas (in fact, canvas's templating is substantially powered by `toolkit.js`).

This view also removes from the list when they are clicked.

```javascript
@cv.view('wordList', {
	data: ['Foo', 'Bar', 'Garden', 'Butcher'],
	template: data =>
		<ul>
			{ tk.comp(data, word => <li>{ word }</li>) }
		</ul>
})
class WordListView {
	@cv.event('li')
	removeWord(el) {
		this.data.splice(el.index(), 1);
	}
}
```