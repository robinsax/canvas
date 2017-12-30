# canvas

A full-stack web application framework in Python and PostgreSQL.

### Installing

```xml
<VirtualHost *:80>
	ServerAdmin $you

	DocumentRoot /var/www
		
	WSGIDaemonProcess site user=$apache_user group=$apache_group threads=10
	WSGIScriptAlias / /var/www/canvas_wsgi.py
	<Directory /var/www>
		WSGIProcessGroup site
		WSGIApplicationGroup %{GLOBAL}
		Require all granted
    </Directory>

	ErrorLog ${APACHE_LOG_DIR}/error.log

	LogLevel debug

	CustomLog ${APACHE_LOG_DIR}/custom.log combined
</VirtualHost>
```

*TODO: This README*