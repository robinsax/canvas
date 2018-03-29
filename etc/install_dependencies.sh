echo "Installing canvas dependencies..."

apt-get update
apt-get install python3-pip postgresql nodejs npm -y
npm update npm

echo "Done"
