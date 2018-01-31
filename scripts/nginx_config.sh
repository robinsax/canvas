#   nginx configuration.
#   Takes <domain> <user>.
cat ./docs/templates/uwsgi_config.conf | sed "s/@user/$2/g" | sed "s/@domain/$1/g" > /etc/nginx/sites-available/canvas
