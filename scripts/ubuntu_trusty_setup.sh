#	Package install script for Ubuntu 14.04 LTS
#	PLACEHOLD

echo "Installing Python 3.6. and Pip"
#   Add the Python 3.6 backport repository (Thanks Jon.).
add-apt-repository ppa:jonathonf/python-3.6 -y
apt-get update
#   Install Python.
apt-get install python3.6 postgresql -y
#   Install Pip.
curl https://bootstrap.pypa.io/get-pip.py | python3.6

echo "Installing Python package dependencies."
#   Install package requirements.
/usr/bin/yes | sudo python3.6 -m pip install -r ./requirements.txt

#   Create settings if it doesn't exist.
if [ ! -f ./settings.json ]; then
	echo "Creating default settings; DO NOT USE THIS CONFIGURATION IN PRODUCTION."
	cp -f ./default_settings.json ./settings.json
fi

echo "Configuring Postgres"
python3.6 ./scripts/write_setup_sql.py | sudo -u postgres psql

