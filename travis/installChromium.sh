#!/bin/bash -ev

# We need a specific version of chromium and chromedriver for tests to pass.
#  These browsers keep changing in ways that break our tests.
#  To install a specific version of chromium-browser: https://www.chromium.org/getting-involved/download-chromium
#  For chromedriver: https://sites.google.com/a/chromium.org/chromedriver/downloads



mkdir -p $HOME/bin
mkdir -p $HOME/opt/chromium
[ -e $HOME/testdownloads ] || mkdir -p $HOME/testdownloads 

cd $HOME/opt/chromium

if [ ! -e $HOME/testdownloads/chromium-50.0.2661.0.zip ]; then
    wget -nv -O $HOME/testdownloads/chromium-50.0.2661.0.zip 'https://www.googleapis.com/download/storage/v1/b/chromium-browser-snapshots/o/Linux_x64%2F378083%2Fchrome-linux.zip?generation=1456540849047000&alt=media'
fi 
unzip $HOME/testdownloads/chromium-50.0.2661.0.zip
mv chrome-linux/chrome_sandbox chrome-linux/chrome-sandbox
ln -fs $PWD/chrome-linux/chrome-wrapper $HOME/bin/chromium-browser

if [ ! -e $HOME/testdownloads/chromedriver-2.22.zip ]; then
    wget -nv -O $HOME/testdownloads/chromedriver-2.22.zip http://chromedriver.storage.googleapis.com/2.22/chromedriver_linux64.zip 
fi
unzip $HOME/testdownloads/chromedriver-2.22.zip -d $HOME/bin
chmod u+x $HOME/bin/chromedriver


export PATH=$HOME/bin:$PATH
