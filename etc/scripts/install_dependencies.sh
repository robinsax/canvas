echo "Installing canvas dependencies..."
#	Install applications.
apt-get update
apt-get install python3-pip postgresql nodejs -y
#	Install Python packages.
pip3 install -r requirements.txt -y
#	Install Babel.
npm install -g --save-dev babel-cli babel-preset-es2015
echo "Done"
