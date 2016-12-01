# -*- mode: ruby -*-
# vi: set ft=ruby :

# To use vagrant on ubuntu 16.04:
#  apt-get install vagrant vagrant-lxc vagrant-cachier
#  cd <where VagrantFile is>
#  vagrant up
#  vagrant ssh

Vagrant.require_version ">= 1.8.1", "< 1.8.9999"

# From https://gist.github.com/juanje/3797297
# (vagrant-cachier does not work with docker & Dockerfile so we roll our own)
def local_cache(cache_name)
  cache_dir = Vagrant::Environment.new.home_path.join('cache', cache_name)
  cache_dir.mkpath unless cache_dir.exist?
  cache_dir
end

def exists?(name)
  `which #{name}`
  $?.success?
end

Vagrant.configure(2) do |config|
  config.vm.hostname = 'reahl-development-machine'

  #https://www.vagrantup.com/docs/providers/basic_usage.html
  config.vm.provider "lxc"
  config.vm.provider "docker"
  config.vm.provider "virtualbox"

  config.vm.provider :lxc do |lxc, override|
    override.vm.box = "nhinds/xenial64"
    if exists? "lxc-ls"
      LXC_VERSION = `lxc-ls --version`.strip unless defined? LXC_VERSION
      if LXC_VERSION >= "2.0.0"
        lxc.backingstore = 'dir'
      end
    end
  end

  config.vm.provider :virtualbox do |vb, override|
    override.vm.box = "ubuntu/xenial64"
  end

  config.vm.provider :docker do |docker, override|
    #docker.image = 'ubuntu:16.04'
    #docker.cmd = ["/sbin/my_init", "--enable-insecure-key"]
#    docker.cmd = ["/sbin/my_init"]
    docker.build_dir = "."
    docker.remains_running = true
    docker.has_ssh = true
#    override.ssh.port = 22
  end
  
  config.vm.synced_folder local_cache('pip-old'), "/tmp/.cache/pip/"
  config.vm.synced_folder local_cache('testdownloads'), "/tmp/testdownloads"
                         
  config.vm.network "forwarded_port", guest: 8000, host: 8000
  config.vm.network "forwarded_port", guest: 8363, host: 8363

  config.ssh.forward_x11 = true

  config.vm.provision "shell", inline: <<-SHELL
    apt-get update
    apt-get install -y python3 python3-virtualenv virtualenvwrapper python3-dev gcc cython libxml2-dev libxslt-dev libsqlite3-0 sqlite3 postgresql-server-dev-all zlib1g-dev libfreetype6-dev equivs openssh-client dpkg-dev unzip git postgresql libyaml-dev screen

    # These are for chromium-browser and chromedriver:
    apt-get install -y gconf-service libasound2 libatk1.0-0 libc6 libcairo2 libcups2 libdbus-1-3 libexpat1 libfontconfig1 libfreetype6 libgcc1 libgconf-2-4 libgdk-pixbuf2.0-0 libglib2.0-0 libgnome-keyring0 libgtk2.0-0 libnspr4 libnss3 libpam0g libpango-1.0-0 libpangocairo-1.0-0 libpangoft2-1.0-0 libstdc++6 libx11-6 libxcomposite1 libxcursor1 libxdamage1 libxext6 libxfixes3 libxi6 libxrandr2  libxrender1 libxss1 libxtst6 zlib1g bash libnss3 xdg-utils 
    # liblcms1-dev -> liblcms2-dev
    # libjpeg62-dev -> libjpeg62-turbo-dev

    # For X11 forwarding to work:
    apt-get install xauth
  SHELL

  config.vm.provision "shell", privileged: false, inline: <<-SHELL
    ln -fs /tmp/testdownloads $HOME/testdownloads
    mkdir -p $HOME/.cache
    ln -fs /tmp/.cache/pip $HOME/.cache/pip
    cd /vagrant
    echo "export REAHLWORKSPACE=\\\$HOME" >> $HOME/.profile
    echo "export EMAIL=noone@example.org" >> $HOME/.profile
    echo "export DEBFULLNAME=\\"Travis Tester\\"" >> $HOME/.profile
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
    sudo /etc/init.d/postgresql start
    sudo su - postgres -c "createuser --superuser $USER"
    reahl-control createdb reahl-web/etc
  SHELL
end

