#	uWSGI configuration. Takes username as the sole parameter.
cp ./docs/templates/uwsgi_config.ini ./canvas_uwsgi.ini
cat ./docs/templates/uwsgi_config.conf | sed "s/@user/$1/g" > /etc/init/canvas.conf

