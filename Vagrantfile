# -*- mode: ruby -*-
# vi: set ft=ruby :

# To use vagrant on ubuntu:
#  apt-get install vagrant vagrant-lxc vagrant-cachier
#  cd <where VagrantFile is>
#  vagrant up
#  vagrant ssh

Vagrant.require_version ">= 1.8.1"

Vagrant.configure(2) do |config|
#  config.vm.box = "reahl/xenial64"
  config.vm.box = "reahl/bionic64"

  config.vm.network "forwarded_port", guest: 8000, host: 8000, auto_correct: true
  config.vm.network "forwarded_port", guest: 8363, host: 8363, auto_correct: true

  config.vm.provision "shell", privileged: true, inline: <<-SHELL
    apt-get install -y --no-install-recommends plantuml inkscape
  SHELL

  config.vm.provision "shell", privileged: false, inline: <<-SHELL
    cd /vagrant
    python scripts/bootstrap.py --script-dependencies && python scripts/bootstrap.py --pip-installs
    reahl createdb reahl-web/etc
    pip install pillow sphinx sphinxcontrib-plantuml graphviz
  SHELL
end

