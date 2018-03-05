loader.attach class ConfigComponent
	constructor: (core) ->
		core.palettes = JSON.parse '{{ config.styling.palettes|json(camelize_keys=True) }}'
		core.breakpoints = JSON.parse '{{ config.styling.breakpoints|json }}'
