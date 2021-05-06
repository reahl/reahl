#!/bin/sh

mkdir -p $HOME/testdownloads
if [ ! -e $HOME/testdownloads/ngrok-stable-linux-amd64.zip ]; then
    wget -nv -O $HOME/testdownloads/ngrok-stable-linux-amd64.zip https://bin.equinox.io/c/4VmDzA7iaHb/ngrok-stable-linux-amd64.zip
fi 
unzip $HOME/testdownloads/ngrok-stable-linux-amd64.zip -d $HOME/bin
