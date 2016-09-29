#!/bin/bash

# We need a specific version of chromium and chromedriver for tests to pass.
#  These browsers keep changing in ways that break our tests.
#  To install a specific version of chromium-browser: https://www.chromium.org/getting-involved/download-chromium
#  For chromedriver: https://sites.google.com/a/chromium.org/chromedriver/downloads


set -e

mkdir -p $HOME/bin
mkdir -p $HOME/opt/chromium

cd $HOME/opt/chromium
wget -O chromium-50.0.2661.0.zip 'https://www.googleapis.com/download/storage/v1/b/chromium-browser-snapshots/o/Linux_x64%2F378083%2Fchrome-linux.zip?generation=1456540849047000&alt=media'
unzip chromium-50.0.2661.0.zip
mv chrome-linux/chrome_sandbox chrome-linux/chrome-sandbox
ln -fs $PWD/chrome-linux/chrome-wrapper $HOME/bin/chromium-browser

wget -O - http://chromedriver.storage.googleapis.com/2.22/chromedriver_linux64.zip | gunzip -c > $HOME/bin/chromedriver
chmod u+x $HOME/bin/chromedriver


export PATH=$HOME/bin:$PATH
