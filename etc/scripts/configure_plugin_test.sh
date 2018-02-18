#	Plugin test auto-configuration for Travis builds.

python3.6 canvas --set_plugin_dir ..
python3.6 canvas --use_plugins set $plugin_names
