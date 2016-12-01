# -*- mode: ruby -*-
# vi: set ft=ruby :

# To use vagrant on ubuntu 16.04:
#  apt-get install vagrant vagrant-lxc vagrant-cachier
#  cd <where VagrantFile is>
#  vagrant up
#  vagrant ssh

Vagrant.require_version ">= 1.8.1"

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
#    docker.cmd = ["/sbin/my_init"]
    docker.build_dir = "."
    docker.remains_running = true
    docker.has_ssh = true
  end
  
  config.vm.synced_folder local_cache('pip-old'), "/tmp/.cache/pip/"
  config.vm.synced_folder local_cache('testdownloads'), "/tmp/testdownloads"
                         
  config.vm.network "forwarded_port", guest: 8000, host: 8000
  config.vm.network "forwarded_port", guest: 8363, host: 8363

  config.ssh.forward_x11 = true

  config.vm.provision "shell", inline: "/vagrant/scripts/installDebs.sh"
  config.vm.provision "shell", privileged: false, inline: <<-SHELL
    ln -fs /tmp/testdownloads $HOME/testdownloads
    mkdir -p $HOME/.cache
    ln -fs /tmp/.cache/pip $HOME/.cache/pip
    cd /vagrant
    ./scripts/setupDevEnv.sh
  SHELL
end

