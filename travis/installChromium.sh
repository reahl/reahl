#!/bin/bash -ev

# We need a specific version of chromium and chromedriver for tests to pass.
#  These browsers keep changing in ways that break our tests.
#  To install a specific version of chromium-browser: https://www.chromium.org/getting-involved/download-chromium
#  For chromedriver: https://sites.google.com/a/chromium.org/chromedriver/downloads

#https://www.chromium.org/getting-involved/download-chromium
# Read he above to get a buildnumber for the chrome version you choose
# https://commondatastorage.googleapis.com/chromium-browser-snapshots/index.html?prefix=Linux_x64/722269/
CHROMIUM_VERSION='80.0.3987'
CHROMIUM_FULL_VERSION='80.0.3987.136'
CHROMIUM_LOCAL_FILENAME='chromium-'$CHROMIUM_FULL_VERSION'.zip'
#CHROMIUM_BRANCH_BASE_POSITION=722274 #this was not found, so decreasing the number to find a hit
#CHROMIUM_BRANCH_BASE_POSITION=722269
CHROMIUM_DOWNLOAD_URL='https://www.googleapis.com/download/storage/v1/b/chromium-browser-snapshots/o/Linux_x64%2F722269%2Fchrome-linux.zip?generation=1575587722227802&alt=media'
XXXCHROME_DRIVER_DOWNLOAD_URL='https://www.googleapis.com/download/storage/v1/b/chromium-browser-snapshots/o/Linux_x64%2F722269%2Fchromedriver_linux64.zip?generation=1575587729061861&alt=media'

#Results (310.38s):
#     540 passed
#       5 failed
#         - reahl/web_dev/test_security.py:56 test_serving_security_sensitive_widgets[web_fixture0]
#         - reahl/web_dev/bootstrap/test_cueinput.py:43 test_cue_input_display_basics[web_fixture0-cue_input_fixture0]
#         - reahl/web_dev/bootstrap/test_cueinput.py:73 test_cue_is_visible_when_js_disabled[web_fixture0-cue_input_fixture0]
#         - reahl/web_dev/bootstrap/test_files.py:137 test_file_input_basics[web_fixture0-file_input_fixture0]
#         - reahl/web_dev/bootstrap/test_files.py:156 test_i18n[web_fixture0-file_input_fixture0]


#https://chromedriver.chromium.org/downloads/version-selection
#Here are the steps to select the version of ChromeDriver to download:
#
#    First, find out which version of Chrome you are using. Let's say you have Chrome 72.0.3626.81.
#    Take the Chrome version number, remove the last part, and append the result to URL "https://chromedriver.storage.googleapis.com/LATEST_RELEASE_". For example, with Chrome version 72.0.3626.81, you'd get a URL "https://chromedriver.storage.googleapis.com/LATEST_RELEASE_72.0.3626".
#    Use the URL created in the last step to retrieve a small file containing the version of ChromeDriver to use. For example, the above URL will get your a file containing "72.0.3626.69". (The actual number may change in the future, of course.)
#    Use the version number retrieved from the previous step to construct the URL to download ChromeDriver. With version 72.0.3626.69, the URL would be "https://chromedriver.storage.googleapis.com/index.html?path=72.0.3626.69/".
#    After the initial download, it is recommended that you occasionally go through the above process again to see if there are any bug fix releases.

CHROME_DRIVER_PATCH_URL='https://chromedriver.storage.googleapis.com/LATEST_RELEASE_'$CHROMIUM_VERSION
CHROME_DRIVER_FULL_VERSION=$(wget -O - $CHROME_DRIVER_PATCH_URL)
CHROME_DRIVER_DOWNLOAD_URL='https://chromedriver.storage.googleapis.com/'$CHROME_DRIVER_FULL_VERSION'/chromedriver_linux64.zip'
CHROME_DRIVER_LOCAL_FILENAME=chromedriver-$CHROME_DRIVER_FULL_VERSION.zip


mkdir -p $HOME/bin
mkdir -p $HOME/opt/chromium
[ -e $HOME/testdownloads ] || mkdir -p $HOME/testdownloads 

cd $HOME/opt/chromium
if [ ! -e '$HOME/testdownloads/$CHROMIUM_LOCAL_FILENAME' ]; then
    wget -nv -O $HOME/testdownloads/$CHROMIUM_LOCAL_FILENAME $CHROMIUM_DOWNLOAD_URL
fi 
unzip $HOME/testdownloads/$CHROMIUM_LOCAL_FILENAME
mv chrome-linux/chrome_sandbox chrome-linux/chrome-sandbox
ln -fs $PWD/chrome-linux/chrome-wrapper $HOME/bin/chromium-browser

if [ ! -e '$HOME/testdownloads/$CHROME_DRIVER_LOCAL_FILENAME' ]; then
    wget -nv -O $HOME/testdownloads/$CHROME_DRIVER_LOCAL_FILENAME $CHROME_DRIVER_DOWNLOAD_URL
fi
unzip $HOME/testdownloads/$CHROME_DRIVER_LOCAL_FILENAME -d $HOME/bin
chmod u+x $HOME/bin/chromedriver


export PATH=$HOME/bin:$PATH
