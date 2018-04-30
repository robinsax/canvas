# canvas

[![Build Status](https://travis-ci.org/robinsax/canvas.svg?branch=master)](https://travis-ci.org/robinsax/canvas)
[![Coverage Status](https://coveralls.io/repos/github/robinsax/canvas/badge.svg?branch=master)](https://coveralls.io/github/robinsax/canvas?branch=master)

A full-stack web application framework for building modern web products simply.

## What's it like?

canvas is designed for minimalism and extensibility. 
*Especially its documentation...* (I'm working on this).

The following code samples define a Breakfast model, an API endpoint that
serves an instance of it, and a view that displays it.

The model and controller:

```python
#   Import canvas.
import canvas as cv

#   Create a breakfast model.
@cv.model('breakfasts', {
    'id': model.Column('uuid', primary_key=True),
    'name': model.Column('text', (
		cv.NotNullConstraint(),
	)),
    'ingredients': model.Column('json')
})
class Breakfast:

    def __init__(self, name, ingredients):
        self.name, self.ingredients = name, ingredients

#   Create an initialization function that cooks a breakfast if there isn't
#   one already.
@cv.on_init
def cook_breakfast():
    session = cv.create_session()

    if not session.query(Breakfast, one=True):
        breakfast = Breakfast('Bacon and Eggs', ['Bacon', 'Eggs'])
        session.save(breakfast).commit()

#   Create an API endpoint that serves breakfast.
@cv.endpoint('/api/breakfast')
class BreakfastEndpoint:

    def on_get(self, context):
        breakfast = context.session.query(Breakfast, one=True)
        return cv.create_json('success', cv.dictize(breakfast))
```

The view:

```javascript
//  Define a breakfast view.
@cv.view({
    dataSource: '/api/breakfast',
    template: (breakfast) => 
        <article class="breakfast">
            <em>Breakfast is served...</em>
            <h1>{ breakfast.name }</h1>
            <ul>
                { tk.comp(breakfast.ingredients, (ingredient) => <li>{ ingredient }</li>) }
            </ul>
            <button>Eat!</button>
        </article>
})
class BreakfastView {
    @cv.event('button')
    eat() {
        alert('Yum!');
    }
}
```

## Setup

The following setup instructions are intended for Ubuntu 14.04 LTS+.

Download and install canvas:

```bash
#   Download and enter this repository.
git clone https://github.com/robinsax/canvas.git
cd canvas

#   Install Python 3, Pip, Node JS, NPM, and PostgreSQL.
sudo ./etc/install_dependencies.sh
#   Initialize the canvas installation.
sudo python3 canvas --init
```

You can now configure canvas by editing `settings.json`.

If you have not already created your database and user, you can run the
following to do so:

```bash
python3 canvas --write-setup-sql | sudo -u postgres psql
```

*Note*: To see the complete list of command line options, simply run `python3 canvas`.

### Running the tests

canvas's unit tests are invoked with:

```bash
python3 canvas --test
```

### Serving for development

You can start canvas's development server with:

```bash
python3 canvas --serve 80
```

An empty canvas instance will then be served at `http://localhost`.

## Use

### Plugins

canvas web applications are implemented as one or more plugins. Plugins are
stored in a shared plugin folder (by default `../canvas_plugins`) and
activated in configuration.

To create a plugin in the configured plugin directory, run:

```bash
python3 canvas --create-plugin <plugin_name>
```

To activate a plugin, modify the appropriate entry of `settings.json`, or run:

```bash
python3 canvas --config "plugins.activated=<plugin_name>,"
```

For more in depth documentation about developing web applications with canvas, 
see the `./docs` directory of this repository.
