# canvas

[![Build Status](https://travis-ci.org/robinsax/canvas.svg?branch=master)](https://travis-ci.org/robinsax/canvas)

A full-stack web application framework written in Python and JavaScript.

### Setup 

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
* [users](https://github.com/robinsax/canvas-pl-users) - Extensible skeleton user model with authorization integration. 
  <br>[![Build status](https://travis-ci.org/robinsax/canvas-pl-users.svg?branch=master)](https://travis-ci.org/robinsax/canvas-pl-users)
* [deferral](https://github.com/robinsax/canvas-pl-deferral) - Scheduled and asynchronous code execution.
  <br>[![Build status](https://travis-ci.org/robinsax/canvas-pl-deferral.svg?branch=master)](https://travis-ci.org/robinsax/canvas-pl-deferral)
* [email](https://github.com/robinsax/canvas-pl-email) - SMTP-based email templating and dispatch.
  <br>[![Build status](https://travis-ci.org/robinsax/canvas-pl-email.svg?branch=master)](https://travis-ci.org/robinsax/canvas-pl-email)

To create a plugin in the configured plugin directory, run:
```bash
python3.6 ./scripts/create_plugin_template.py <plugin_name>
```

*To be continued...*
