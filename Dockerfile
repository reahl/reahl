FROM phusion/baseimage:0.9.19
#MAINTAINER Anatoly Bubenkov "bubenkoff@gmail.com"

ENV HOME /root

# enable ssh
RUN rm -f /etc/service/sshd/down

# Use baseimage-docker's init system.
CMD ["/sbin/my_init"]

RUN apt-get update

RUN apt-get install -y openssh-server wget lsb-release sudo

EXPOSE 22

# Create and configure vagrant user
RUN useradd --create-home -s /bin/bash vagrant
WORKDIR /home/vagrant

# Configure SSH access
RUN echo -n 'vagrant:vagrant' | chpasswd
RUN mkdir -p /home/vagrant/.ssh
RUN chmod 0700 /home/vagrant/.ssh
RUN echo "ssh-rsa AAAAB3NzaC1yc2EAAAABIwAAAQEA6NF8iallvQVp22WDkTkyrtvp9eWW6A8YVr+kz4TjGYe7gHzIw+niNltGEFHzD8+v1I2YJ6oXevct1YeS0o9HZyN1Q9qgCgzUFtdOKLv6IedplqoPkcmF0aYet2PkEDo3MlTBckFXPITAMzF8dJSIFo9D8HfdOV0IAdx4O7PtixWKn5y2hMNG0zQPyUecp4pzC6kivAIhyfHilFR61RGL+GPXQ2MWZWFYbAGjyiYJnAmCP3NOTd0jMZEnDkbUvxhMmBYSdETk1rRgm+R4LOzFUGaHqHDLKLX+FIPKcF96hrucXzcWyLbIbEgE98OHlnVYCzRdK8jlqm8tehUc9c9WhQ== vagrant insecure public key" > /home/vagrant/.ssh/authorized_keys
RUN chown -R vagrant:vagrant /home/vagrant/.ssh
RUN chmod -R 0600 /home/vagrant/.ssh/*

# Enable passwordless sudo for the "vagrant" user
RUN echo 'vagrant ALL=NOPASSWD: ALL' > /etc/sudoers.d/vagrant
RUN chmod 0440 /etc/sudoers.d/vagrant


# Clean up APT when done.

#RUN apt-get clean && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*
