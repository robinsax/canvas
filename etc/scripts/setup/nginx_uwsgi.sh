#   Full configuration for hosting with uWSGI + nginx. Takes <user> <domain>.
#
#	Run ./etc/scripts/install_dependencies.sh first.

apt-get update
/usr/bin/yes | apt-get install uwsgi nginx

python3 ./etc/scripts/write_setup_sql.py | sudo -u postgres psql

#	Configure uWSGI.
cp ./etc/configs/uwsgi_config.ini ./canvas_uwsgi.ini
cat ./etc/configs/uwsgi_config.conf | sed "s/@user/$1/g" > /etc/init/canvas.conf

#   Configure nginx.
cat ./etc/configs/nginx_config | sed "s/@user/$1/g" | sed "s/@domain/$2/g" > /etc/nginx/sites-available/canvas
ln -s /etc/nginx/sites-available/canvas /etc/nginx/sites-enabled

mkdir /var/log/uwsgi
touch /var/log/uwsgi/all.log
#   Setup uWSGI logging.
chmod a+w /var/log/uwsgi/all.log

#   Start nginx.
/etc/init.d/nginx start

#	TODO: Run uwsgi as service.
