#!/bin/sh -ex


# Setup environment
echo "if [ -z \"\$DISPLAY\" ]; then export DISPLAY=:100; fi" >> $HOME/.profile
echo "export REAHLWORKSPACE=\$HOME" >> $HOME/.profile
echo "export EMAIL=noone@example.org" >> $HOME/.profile
echo "export DEBFULLNAME=\"Travis Tester\"" >> $HOME/.profile
echo "export DEBEMAIL=\$EMAIL" >> $HOME/.profile
echo "export PACKAGESIGNKEYID=DE633F86" >> $HOME/.profile
echo "export PATH=\$HOME/bin:\$PATH" >> $HOME/.profile
echo "export PGPASSWORD=reahl" >> $HOME/.profile
echo "export MYSQL_PWD=reahl" >> $HOME/.profile
echo "export REAHL_TEST_CONNECTION_URI='postgresql://reahl:reahl@postgres/reahl'" >> $HOME/.profile
echo "#export REAHL_TEST_CONNECTION_URI='mysql://reahl:reahl@mysql/reahl'" >> $HOME/.profile
. $HOME/.profile

cat <<'EOF' >> $HOME/.profile

# Start xpra if necessary
if ! xdpyinfo -display $DISPLAY 1>/dev/null 2>&1; then 
  echo "There is no display server running on $DISPLAY, starting xpra"
  xpra start --sharing=yes $DISPLAY 1>/dev/null 2>&1
fi

# Show fingerprints of current host
echo 
echo "The fingerprints of the host are:"
echo "================================="
for i in $(ls /etc/ssh/ssh_host_*.pub); do
    for e in md5 sha256; do
        ssh-keygen -l -E $e -f $i;
    done
done
EOF

cat << 'EOF' >> $HOME/.screenrc
hardstatus on
hardstatus alwayslastline
hardstatus string "%{.bW}%-w%{.rW}%n %t%{-}%+w %=%{..G} %H %{..Y} %m/%d %C%a "
EOF

# User installs and config
./travis/createTestSshKey.sh
./travis/createTestGpgKey.sh
./travis/configurePip.sh
./travis/setupTestGit.sh


