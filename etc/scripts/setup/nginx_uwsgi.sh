#   Full configuration for hosting with uWSGI + nginx. Takes <user> <domain>.
#   Install dependencies.
apt-get update
/usr/bin/yes | apt-get install python3-pip nginx postgresql
/usr/bin/yes | pip3 install -r requirements.txt
/usr/bin/yes | pip3 install uwsgi

#	Copy relevant configuration to root.
cp ./etc/configs/canvas_uwsgi.ini ./canvas_uwsgi.ini

#   Configure Postgres.
python3 ./scripts/write_setup_sql.py | sudo -u postgres psql

#   Configure uWSGI.
cp ./docs/templates/uwsgi_config.ini ./canvas_uwsgi.ini
cat ./docs/templates/uwsgi_config.conf | sed "s/@user/$1/g" > /etc/init/canvas.conf

#   Configure nginx.
cat ./docs/templates/nginx_config | sed "s/@user/$1/g" | sed "s/@domain/$2/g" > /etc/nginx/sites-available/canvas
ln -s /etc/nginx/sites-available/canvas /etc/nginx/sites-enabled

mkdir /var/log/uwsgi
touch /var/log/uwsgi/all.log
#   Setup uWSGI logging.
chmod a+w /var/log/uwsgi/all.log

#   Start nginx.
/etc/init.d/nginx start

#TODO: Run uwsgi as service.