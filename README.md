# canvas

[![Build Status](https://travis-ci.org/robinsax/canvas.svg?branch=master)](https://travis-ci.org/robinsax/canvas)

[![Coverage Status](https://coveralls.io/repos/github/robinsax/canvas/badge.svg?branch=master)](https://coveralls.io/github/robinsax/canvas?branch=master)

A full-stack web application framework written in Python and JavaScript.

## What's it like?

canvas is designed for minimalism and extensibility. The following code sample
defines an API endpoint that serves breakfast. Don't worry if you don't totally understand
it; it's just a demonstration.

```python
#	Import the 3 primary canvas interfaces.
import canvas as cv

from canvas import model, controllers

#	Create a breakfast model.
@model.schema('breakfasts', {
	'id': model.Column('uuid', primary_key=True),
	'name': model.Column('text'),
	'manifest': model.Column('json')
})
class Breakfast:

	def __init__(self, name, manifest):
		self.name, self.manifest = name, manifest

#	Create an initialization function that cooks a breakfast.
@cv.callback.init
def cook_breakfast():
	session = model.create_session()

	breakfast = Breakfast('Bacon and eggs', {
		'bacon': {'type': 'crispy'},
		'eggs': {'style': 'sunny side up'}
	})
	session.save(breakfast)
	session.commit()

#	Create an API endpoint that serves breakfast.
@cv.register.controller
class BreakfastEndpoint(controllers.APIEndpoint):

	def __init__(self):
		super().__init__('/api/breakfast')

	def get(self, ctx):
		to_serve = ctx['session'].query(Breakfast, one=True)
		return cv.create_json('success', model.dictize(to_serve))
```

## Setup 

The following setup instructions are intended for Ubuntu, however Windows and OSX
are also supported. All WSIG-compliant servers are supported.

First install Postgres and Python 3.6:
```bash
apt-get update
apt-get install postgresql python3.6
```

Then download and set up canvas:
```bash
#	Download this repository.
git clone https://github.com/robinsax/canvas.git

#	Install the Python package requirements.
cd canvas
python3.6 -m pip install -r requirements.txt
```

To configure canvas, make a copy of `default_settings.json` called `settings.json`
and in it update at least the `database` section and `cookie_secret_key` value.

If you have not yet configured the user and database within Postgres, you can
run the following to do so:
```bash
python3.6 ./etc/scripts/write_setup_sql.py | sudo -u postgres psql postgres
```

### Running the tests

canvas's unit tests are invoked with:
```
python3.6 canvas --run_tests
```

###	Serving for development

You can start canvas's development server with:
```bash
python3.6 canvas --serve 80
```

An empty canvas instance will then be served at http://localhost.

*Note:* The canvas development server is not suitable for a production environment.

## Use

### Plugins

canvas web applications are implemented as one or more plugins. Plugins are stored
in a shared plugin folder (by default `../canvas_plugins`) and activated in
configuration.

Some existing plugins are:
* [users](https://github.com/robinsax/canvas-pl-users) - An extensible user model and authorization interface. 
* [robots](https://github.com/robinsax/canvas) - Per-controller `robots.txt` management.
* [deferral](https://github.com/robinsax/canvas-pl-deferral) - Scheduled and asynchronous code execution.
* [smtpmail](https://github.com/robinsax/canvas-pl-smtpmail) - Email templating and dispatch via SMTP.
* [xmlcolumns](https://github.com/robinsax/canvas-pl-xmlcolumns) - XML column type/model attribute via `lxml.etree`.

To create a plugin in the configured plugin directory, run:
```bash
python3.6 canvas --create_plugin <plugin_name>
```

To activate some plugins, and their dependencies, run:
```bash
python3.6 canvas --use_plugins set <plugin_1>, ..., <plugin_n>
```

For more in depth documentation about developing plugins for canvas, see the `./docs`
directory of this repository.
