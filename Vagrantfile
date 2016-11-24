# -*- mode: ruby -*-
# vi: set ft=ruby :

# NOTE: This file is just a little experiment I played with and want to leave hanging around.
#   It would be nice if we can provision development environments via Vagrant (or something)
#   instead of the chroots we are currently developing in. Also, out chroots are based on 
#   trusty where we do not have python3.5 so we cannot currently develop past python3.4.
#
# This Vagrant file is a start towards using the vagrant and vagrant-lxc packages on
# ubuntu 16.04 for setting up a development environment that can be used for python3.5
#
# It is incomplete, there's lots of stuff from .travis.yml that it would also need
# to do and I don't want to duplicate it all here.
#
# There are also slight variations that would have to be catered for.
# Like, slightly different versions of packages, some packages that are installed on 
# travis, but not here, etc. Also things like the vagrant user that needs to be set up 
# as postgresql superuser etc.
#
# This is almost usable now: just need to create the postgres user with a password.
#
# To use vagrant on ubuntu 16.04:
#  apt-get install vagrant vagrant-lxc vagrant-cachier
#  cd <where VagrantFile is>
#  vagrant up
#  vagrant ssh


# From https://gist.github.com/juanje/3797297 
def local_cache(basebox_name)
  cache_dir = Vagrant::Environment.new.home_path.join('cache', 'pip-old', basebox_name)
  cache_dir.mkpath unless cache_dir.exist?
  cache_dir
end

# All Vagrant configuration is done below. The "2" in Vagrant.configure
# configures the configuration version (we support older styles for
# backwards compatibility). Please don't change it unless you know what
# you're doing.
Vagrant.configure(2) do |config|
  # The most common configuration options are documented and commented below.
  # For a complete reference, please see the online documentation at
  # https://docs.vagrantup.com.

  # Every Vagrant development environment requires a box. You can search for
  # boxes at https://atlas.hashicorp.com/search.
  #config.vm.box = "debian/jessie64"
  config.vm.box = "nhinds/xenial64"

  if Vagrant.has_plugin?("vagrant-cachier")
    config.cache.scope = :box
    config.cache.enable :generic, { :cache_dir => "/home/vagrant/testdownloads" }
#    config.cache.enable :pip 
  end

  config.vm.synced_folder local_cache(config.vm.box), "/home/vagrant/.cache/pip/"
                         

  # Disable automatic box update checking. If you disable this, then
  # boxes will only be checked for updates when the user runs
  # `vagrant box outdated`. This is not recommended.
  # config.vm.box_check_update = false

  # Create a forwarded port mapping which allows access to a specific port
  # within the machine from a port on the host machine. In the example below,
  # accessing "localhost:8080" will access port 80 on the guest machine.
  config.vm.network "forwarded_port", guest: 8000, host: 8000
  config.vm.network "forwarded_port", guest: 8363, host: 8363

  # Create a private network, which allows host-only access to the machine
  # using a specific IP.
  # config.vm.network "private_network", ip: "192.168.33.10"

  # Create a public network, which generally matched to bridged network.
  # Bridged networks make the machine appear as another physical device on
  # your network.
  # config.vm.network "public_network"

  # Share an additional folder to the guest VM. The first argument is
  # the path on the host to the actual folder. The second argument is
  # the path on the guest to mount the folder. And the optional third
  # argument is a set of non-required options.
  # config.vm.synced_folder "../data", "/vagrant_data"

  # Provider-specific configuration so you can fine-tune various
  # backing providers for Vagrant. These expose provider-specific options.
  # Example for VirtualBox:
  #
  # config.vm.provider "virtualbox" do |vb|
  #   # Display the VirtualBox GUI when booting the machine
  #   vb.gui = true
  #
  #   # Customize the amount of memory on the VM:
  #   vb.memory = "1024"
  # end
  #
  # View the documentation for the provider you are using for more
  # information on available options.

  # Define a Vagrant Push strategy for pushing to Atlas. Other push strategies
  # such as FTP and Heroku are also available. See the documentation at
  # https://docs.vagrantup.com/v2/push/atlas.html for more information.
  # config.push.define "atlas" do |push|
  #   push.app = "YOUR_ATLAS_USERNAME/YOUR_APPLICATION_NAME"
  # end

  config.ssh.forward_x11 = true
  config.ssh.forward_agent = true
  # Enable provisioning with a shell script. Additional provisioners such as
  # Puppet, Chef, Ansible, Salt, and Docker are also available. Please see the
  # documentation for more information about their specific syntax and use.
  config.vm.provision "shell", inline: <<-SHELL
    apt-get update
    apt-get install -y python-virtualenv virtualenvwrapper python-dev gcc cython libxml2-dev libxslt-dev libsqlite3-0 sqlite3 postgresql-server-dev-all zlib1g-dev libfreetype6-dev equivs openssh-client dpkg-dev unzip python3-dev git postgresql-client-9.5 postgresql-9.5 libyaml-dev

    # These are for chromium-browser and chromedriver:
    apt-get install -y gconf-service libasound2 libatk1.0-0 libc6 libcairo2 libcups2 libdbus-1-3 libexpat1 libfontconfig1 libfreetype6 libgcc1 libgconf-2-4 libgdk-pixbuf2.0-0 libglib2.0-0 libgnome-keyring0 libgtk2.0-0 libnspr4 libnss3 libpam0g libpango-1.0-0 libpangocairo-1.0-0 libpangoft2-1.0-0 libstdc++6 libx11-6 libxcomposite1 libxcursor1 libxdamage1 libxext6 libxfixes3 libxi6 libxrandr2  libxrender1 libxss1 libxtst6 zlib1g bash libnss3 xdg-utils 
    # liblcms1-dev -> liblcms2-dev
    # libjpeg62-dev -> libjpeg62-turbo-dev

    # For X11 forwarding to work:
    apt-get install xauth
  SHELL

  config.vm.provision "shell", privileged: false, inline: <<-SHELL
    cd /vagrant
    echo "export REAHLWORKSPACE=\\\$HOME" >> $HOME/.profile
    echo "export EMAIL=noone@example.org" >> $HOME/.profile
    echo "export DEBFULLNAME=\"Travis Tester\"" >> $HOME/.profile
    echo "export DEBEMAIL=\\\$EMAIL" >> $HOME/.profile
    echo "export PACKAGESIGNKEYID=DE633F86" >> $HOME/.profile
    echo "export WORKON_HOME=\\\$HOME/virtualenv" >> $HOME/.profile
    echo "export PATH=\$HOME/bin:\\\$PATH" >> $HOME/.profile
    source $HOME/.profile
    ./travis/installChromium.sh
    ./travis/createTestSshKey.sh
    ./travis/createTestGpgKey.sh
    mkdir -p $HOME/virtualenv
    echo "source /usr/share/virtualenvwrapper/virtualenvwrapper.sh" >> $HOME/.profile
    echo "workon python3.5" >> $HOME/.profile
    source /usr/share/virtualenvwrapper/virtualenvwrapper.sh
    mkvirtualenv -p $(which python3.5) python3.5
    workon python3.5
    python scripts/bootstrap.py --script-dependencies && python scripts/bootstrap.py --pip-installs
    sudo -u postgres createuser --superuser vagrant
    ./travis/setupTestPostgresql.sh
  SHELL
end

