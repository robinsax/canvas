#	Patch versioning issue in CI. Plugin builds will break if we purely bump
#	postgres in Travis config.
sudo pkill -u postgres

echo "Installing canvas dependencies..."

apt-get update
apt-get install python3-pip postgresql nodejs npm -y

/usr/lib/postgresql/10/bin/pg_ctl -D /var/lib/postgresql/10/main -l logfile start

echo "Done"
