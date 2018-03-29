# canvas

[![Build Status](https://travis-ci.org/robinsax/canvas.svg?branch=master)](https://travis-ci.org/robinsax/canvas)
[![Coverage Status](https://coveralls.io/repos/github/robinsax/canvas/badge.svg?branch=master)](https://coveralls.io/github/robinsax/canvas?branch=master)

A full-stack web application framework with modern front-end toolchain.

## What's it like?

canvas is designed for minimalism and extensibility. The following code sample
defines an API endpoint that serves breakfast. Don't worry if you don't totally understand
it; it's just a demonstration.

```python
#	Import canvas.
import canvas as cv

#	Create a breakfast model.
@cv.model('breakfasts', {
	'id': model.Column('uuid', primary_key=True),
	'name': model.Column('text'),
	'manifest': model.Column('json')
}, contructor=True)
class Breakfast: pass

#	Create an initialization function that cooks a breakfast.
@cv.on_init
def cook_breakfast():
	session = cv.create_session()

	breakfast = Breakfast('Bacon and Eggs', {
		'Bacon': {'tasty': True},
		'Eggs': {'style': 'Sunny side up'}
	})
	session.save(breakfast).commit()

#	Create an API endpoint that serves breakfast.
@cv.endpoint('/api/breakfast')
class BreakfastEndpoint:

	def on_get(self, context):
		to_serve = context.session.query(Breakfast, one=True)
		return cv.create_json('success', model.dictize(to_serve))
```

## Setup 

The following setup instructions are intended for Ubuntu, however Windows and OSX
are also supported. All WSIG-compliant servers are supported.

First install Postgres and Python 3:
```bash
apt-get update
apt-get install postgresql python3
```

Then download and set up canvas:
```bash
#	Download this repository.
git clone https://github.com/robinsax/canvas.git

#	Install canvas.
./canvas/etc/scripts/install_dependencies.sh
```

To configure canvas, make a copy of `default_settings.json` called `settings.json`
and in it update at least the `database` and `security` sections.

If you have not yet configured the user and database within Postgres, you can
run the following to do so:
```bash
python3 ./etc/scripts/write_setup_sql.py | sudo -u postgres psql postgres
```

### Running the tests

canvas's unit tests are invoked with:
```
python3 canvas --run_tests
```

###	Serving for development

You can start canvas's development server with:
```bash
python3 canvas --serve 80
```

An empty canvas instance will then be served at http://localhost.

## Use

### Plugins

canvas web applications are implemented as one or more plugins. Plugins are stored
in a shared plugin folder (by default `../canvas_plugins`) and activated in
configuration.

To create a plugin in the configured plugin directory, run:
```bash
python3 canvas --create-plugin <plugin_name>
```

To activate some plugins, and their dependencies, run:
```bash
python3 canvas --use-plugins set <plugin_1>, ..., <plugin_n>
```

For more in depth documentation about developing plugins for canvas, see the `./docs`
directory of this repository.
