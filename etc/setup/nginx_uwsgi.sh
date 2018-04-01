#   Full configuration for hosting with uWSGI + nginx. Takes <user> <domain>.

apt-get update
apt-get install uwsgi nginx -y

#	Configure uWSGI.
cp ./etc/configurations/uwsgi_config.ini ./canvas_uwsgi.ini
cat ./etc/configurations/uwsgi_config.conf | sed "s/@user/$1/g" > /etc/init/canvas.conf

#   Configure nginx.
cat ./etc/configurations/nginx_config | sed "s/@user/$1/g" | sed "s/@domain/$2/g" > /etc/nginx/sites-available/canvas
ln -s /etc/nginx/sites-available/canvas /etc/nginx/sites-enabled

touch /var/log/uwsgi/all.log
#   Setup uWSGI logging.
chmod a+w /var/log/uwsgi/all.log

#   Start nginx.
/etc/init.d/nginx start

#	TODO: Run uwsgi as service.
