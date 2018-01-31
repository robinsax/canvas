#   Full configuration for hosting with uWSGI + nginx. Takes <user> <domain>.
#   Install dependencies.
apt-get update
/usr/bin/yes | apt-get install python3-pip nginx postgresql
/usr/bin/yes | pip3 install -r requirements.txt
/usr/bin/yes | pip3 install uwsgi

#   Configure Postgres.
python3 ./scripts/write_setup_sql.py | sudo -u postgres psql

#   Configure uWSGI.
cp ./docs/templates/uwsgi_config.ini ./canvas_uwsgi.ini
cat ./docs/templates/uwsgi_config.conf | sed "s/@user/$1/g" > /etc/init/canvas.conf

#   Configure nginx.
cat ./docs/templates/nginx_config | sed "s/@user/$1/g" | sed "s/@domain/$2/g" > /etc/nginx/sites-available/canvas
ln -s /etc/nginx/sites-available/canvas /etc/nginx/sites-enabled

#   Start nginx.
/etc/init.d/nginx start
