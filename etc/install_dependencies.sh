#	Patch versioning issue in CI. Plugin builds will break if we purely bump
#	postgres in Travis config.
echo "Installing canvas dependencies..."

apt-get update
apt-get install python3-pip postgresql nodejs npm -y

echo "Done"
