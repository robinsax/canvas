#	Package setup script for Ubuntu 14.04 LTS

#   Create settings if it doesn't exist.
if [ ! -f ./settings.json ]; then
	echo "Creating default settings; DO NOT USE THIS CONFIGURATION IN PRODUCTION"
	cp -f ./default_settings.json ./settings.json
fi

echo "Configuring Postgres"
python3 ./scripts/write_setup_sql.py | sudo -u postgres psql

echo "Done"
