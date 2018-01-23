# canvas

[![Build Status](https://travis-ci.org/robinsax/canvas.svg?branch=master)](https://travis-ci.org/robinsax/canvas)

A full-stack web application framework written in Python and JavaScript.

### Setup 

First install Postgres and Python 3.6. On Linux this looks something like:
```bash
apt-get update
apt-get install postgresql python3.6
```

Then download and set up canvas:
```bash
#	Download this repository.
git clone https://github.com/robinsax/canvas.git
cd canvas
#	Install the Python package requirements.
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

You can then start canvas's development server:
```bash
python3.6 canvas --serve 80
```

An empty canvas instance will then be served at http://localhost.

*Note:* The canvas development server is not suitable for a production environment.

### Basic use

canvas web applications are implemented as one or more plugins. Plugins are stored
in a shared plugin folder (by default `../canvas_plugins`) and activated in
configuration.

Some existing plugins are:
* [users](https://github.com/robinsax/canvas-pl-users) - User model and authentication.
* [deferred_work](https://github.com/robinsax/canvas-pl-deferred_work) - Asynchronous and scheduled code execution.

To create a plugin, run:
```bash
python3.6 ./scripts/create_plugin_template.py <target_dir> <plugin_name>
```

*To be continued...*