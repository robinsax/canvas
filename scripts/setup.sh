echo "Installing dependencies"
sudo apt-get update
sudo apt-get install apache2 libapache2-mod-wsgi postgresql python3.6 python3.6-pip
python3.6 -m pip install -r ./requirements.txt

if [! -f ./settings.json ]; then
	echo "Creating default settings"
	cp -f ./default_settings.json ./settings.json
fi
