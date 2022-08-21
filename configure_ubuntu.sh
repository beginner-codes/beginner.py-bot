#!/bin/bash

cd "$(dirname "$0")"

echo "Project directory: $(realpath .)"

echo "Installing Python3 and pip3"
sudo apt-get install python3 python3-pip -y

echo "Installing poetry"
curl -sSL https://raw.githubusercontent.com/python-poetry/poetry/master/get-poetry.py | python3 -

echo "Adding alias python=\"python3\" to ~/.bashrc"
echo "alias python=\"python3\"" >> ~/.bashrc

echo "Adding poetry default installation to ~/.bashrc"
echo "export PATH=\$PATH:$HOME/.poetry/bin" >> ~/.bashrc

echo "Removing python3 virtualenv for poetry compatibility"
sudo apt remove --purge python3-virtualenv -y

echo "Locking poetry..."
poetry lock

echo "Installing poetry dependencies"
poetry install

echo "Copying ./development.example.yaml file to ./development.yaml"
cp ./development.example.yaml ./development.yaml

echo "Put your bot token into the development.yaml file."
echo "For the default database option, use this configuration:"
echo "database:"
echo -e "\tname: \"bpydb\""
echo -e "\tuser: \"postgresadmin\""
echo -e "\thost: \"0.0.0.0\""
echo -e "\tport: \"5432\""
echo -e "\tpass: \"dev-env-password-safe-to-be-public\""
echo -e "\tdriver: \"sqlite\""

echo "Creating run.sh file"
touch run.sh
echo -e "#!/bin/sh\npoetry run python -m beginner" >> run.sh
chmod +x ./run.sh
echo "Use ./run.sh to start the bot!"

exit
