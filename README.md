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
and in it update at least the `database` section (changing the `cookie_secret_key` 
is also highly recommended).

If you have not yet configured the user and database within Postgres, you can
run the following to do so:
```bash
python3.6 ./scripts/write_setup_sql.py | sudo -u postgres psql postgres
```

### Running the tests

canvas's unit tests are invoked with:
```
python3.6 canvas --run_tests
```

###	Serving for development

You can then start canvas's development server with:
```bash
python3.6 canvas --serve 80
```

An empty canvas instance will then be served at http://localhost.

*Note:* The canvas development server is not suitable for a production environment.

## Use

### Plugin basics

canvas web applications are implemented as one or more plugins. Plugins are stored
in a shared plugin folder (by default `../canvas_plugins`) and activated in
configuration.

Some existing plugins are:
* [users](https://github.com/robinsax/canvas-pl-users) - A basic but extensible user model with authorization integration. 
  <br>[![Build Status](https://travis-ci.org/robinsax/canvas-pl-users.svg?branch=master)](https://travis-ci.org/robinsax/canvas-pl-users)
* [deferral](https://github.com/robinsax/canvas-pl-deferral) - Scheduled and asynchronous code execution.
  <br>[![Build Status](https://travis-ci.org/robinsax/canvas-pl-deferral.svg?branch=master)](https://travis-ci.org/robinsax/canvas-pl-deferral)
* [smtpmail](https://github.com/robinsax/canvas-pl-smtpmail) - Email templating and dispatch via SMTP.
  <br>[![Build Status](https://travis-ci.org/robinsax/canvas-pl-smtpmail.svg?branch=master)](https://travis-ci.org/robinsax/canvas-pl-smtpmail)
* [xml_columns](https://github.com/robinsax/canvas-pl-xml_columns) - LXML-based XML column types.
  <br>[![Build Status](https://travis-ci.org/robinsax/canvas-pl-xml_columns.svg?branch=master)](https://travis-ci.org/robinsax/canvas-pl-xml_columns)

To create a plugin in the configured plugin directory, run:
```bash
python3.6 canvas --create_plugin <plugin_name>
```

Plugins are organized as follows. Directories prefixed with * are not automatically generated 
as they may not be required.
```
canvas-pl-<plugin_name>/
	assets/
		# The assets directory contains all non-Python plugin assets.
		*markdown/
			# The root directory searched for markdown files.
		*client/
			# The root directory searched for client-side assets including 
			# Javascript, CSS, LESS, and media.
			*lib/
			*media/
		*templates/
			# The root directory searched for Jinja templates.
			*client/
				# Client-side assets can also be templated with Jinja.
			*components/
				# Component HTML templates.
			*pages/
				# Page HTML templates.
	<plugin_name>/
		# The Python package containing the plugin logic.
		__init__.py
		*model/
		*controllers/
	tests/
		# The Python package containing plugin unit tests.
		__init__.py
	docs/
		# The plugin documentation directory.
		code/
			# The automatically generated code documentation directory.
	# The settings JSON file.
	settings.json
	# A preconfigured Travis CI build configuration with Coveralls
	# integration.
	.travis.yml
	# A preconfigured coverage configuration.
	.coveragerc
```

*To be continued...*
