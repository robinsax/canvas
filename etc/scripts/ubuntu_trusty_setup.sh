#	Package install script for Ubuntu 14.04 LTS.

echo "Installing canvas dependencies..."
#   Add the Python 3.6 backport repository.
add-apt-repository ppa:jonathonf/python-3.6 -y
#	Install applications.
apt-get update
apt-get install python3-pip postgresql nodejs -y
#	Install CoffeeScript and Babel.
npm install --save-dev coffeescript babel-cli babel-preset-es2015
#   Install Pip.
curl https://bootstrap.pypa.io/get-pip.py | python3.6

echo "Installing Python package dependencies"
#   Install package requirements.
/usr/bin/yes | sudo python3.6 -m pip install -r ./requirements.txt

#   Create settings if it doesn't exist.
if [ ! -f ./settings.json ]; then
	echo "Creating default settings; DO NOT USE THIS CONFIGURATION IN PRODUCTION"
	cp -f ./default_settings.json ./settings.json
fi

echo "Configuring Postgres"
python3.6 ./etc/scripts/write_setup_sql.py | sudo -u postgres psql

echo "Done"
