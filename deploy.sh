#!/bin/bash

# Обновление системы
sudo apt-get update
sudo apt-get upgrade -y

# Установка Docker и Docker Compose если их нет
if ! [ -x "$(command -v docker)" ]; then
  echo 'Installing Docker...'
  sudo apt-get install -y apt-transport-https ca-certificates curl software-properties-common
  curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo apt-key add -
  sudo add-apt-repository "deb [arch=amd64] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable"
  sudo apt-get update
  sudo apt-get install -y docker-ce
  sudo usermod -aG docker $USER
  echo 'Docker installed successfully!'
fi

if ! [ -x "$(command -v docker-compose)" ]; then
  echo 'Installing Docker Compose...'
  sudo curl -L "https://github.com/docker/compose/releases/download/v2.24.5/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
  sudo chmod +x /usr/local/bin/docker-compose
  echo 'Docker Compose installed successfully!'
fi

# Запуск приложения
echo 'Building and starting the application...'
docker-compose up -d --build

echo 'Application deployed successfully!'
echo 'You can access it at:'
echo "http://$(hostname -I | awk '{print $1}'):5000" 