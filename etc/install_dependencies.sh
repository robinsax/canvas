#	Patch versioning issue in CI. Plugin builds will break if we purely bump
#	postgres in Travis config.
sudo service postgresql stop

echo "Installing canvas dependencies..."

apt-get update
apt-get install python3-pip postgresql nodejs npm -y

sudo service postgresql start

echo "Done"
