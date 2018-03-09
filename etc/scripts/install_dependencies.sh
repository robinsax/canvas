echo "Installing canvas dependencies..."
#	Install applications.
apt-get update
apt-get install python3-pip postgresql nodejs npm -y
#	Install Python packages.
/usr/bin/yes | pip3 install -r requirements.txt
#	Install Node packages.
cat required_packages | xargs npm install --save-dev 

echo "Done"
