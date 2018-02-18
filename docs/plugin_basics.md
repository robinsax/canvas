##	Plugin basics

###	Creation

canvas web applications are implemented as a collection of plugins. To create a plugin 
in the configured plugin directory, run:
```bash
python3.6 canvas --create_plugin <plugin name>
```

###	What's in a plugin?

Plugins are organized as follows. Directories prefixed with * are not automatically generated 
as they may not be required.
```
canvas-pl-<plugin_name>/
	assets/
		# The assets directory contains all non-Python plugin assets.
		*markdown/
			# The root directory searched for markdown files.
		*client/
			# The root directory searched for client-side assets including Javascript, CSS, 
			# LESS, and media.
			*lib/
			*media/
		*templates/
			# The root directory searched for Jinja templates.
			*client/
				# Client-side assets can also be templated with Jinja.
			*pages/
				# Page HTML templates. 
	<plugin_name>/
		# The Python package containing the plugin logic.
		__init__.py
	tests/
		# The Python package containing plugin unit tests.
		__init__.py
	docs/
		# The plugin documentation directory.
		code/
			# The automatically generated code documentation directory.
	# The settings override file.
	settings.json
	# A preconfigured Travis CI build configuration with Coveralls integration.
	.travis.yml
	# A preconfigured coverage configuration.
	.coveragerc
	# Python packages required by this plugin.
	requirements.txt
	# Other canvas plugins on which this plugin depends.
	dependencies.txt
```

### The plugin package

On startup, canvas imports the python package found in each plugin's root directory with the 
name of that plugin.

Plugins can then import canvas's interfaces and declare controllers, models, callbacks, and
anything else they require.

*Note*: It's often helpful for plugin package organization to have `model` and `controllers`
	packages. To faciliate this strategy, canvas's packages of those names will populate
	their namespace with all registered model and controller classes. This means that plugins
	can access the contents of their instances of these packages through the core instances.
