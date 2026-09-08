#! /bin/sh
# vim:noet:
#
# Vagrant provision script
#

if [ ! -f /root/.provision_updated ] ; then
	yum clean all
	yum makecache fast

	yum install -y deltarpm
	yum update -y

	touch /root/.provision_updated
fi

if [ ! -f /root/.provision_install_deps ] ; then
	yum clean all
	yum makecache fast

	yum install -y centos-release-scl

	yum group install -y "Development Tools"
	yum install -y rh-ruby24-rubygem-bundler rh-ruby24-ruby-devel

	touch /root/.provision_install_deps
fi

if [ ! -f /root/.provision_install_chef ] ; then
	sudo -u vagrant scl enable rh-ruby24 'bundler install --gemfile=/vagrant/chef/Gemfile --path=/home/vagrant/.local/var/lib/chef-bundle'

	[ ! -d /home/vagrant/.local/bin ] && sudo -u vagrant mkdir /home/vagrant/.local/bin
	sudo -u vagrant tee /home/vagrant/.local/bin/berks << 'EOF' > /dev/null
#! /bin/sh
BUNDLE_PATH=/home/vagrant/.local/var/lib/chef-bundle BUNDLE_GEMFILE=/vagrant/chef/Gemfile BUNDLE_DISABLE_SHARED_GEMS="true" scl enable rh-ruby24 "bundler exec berks $@"
EOF
	sudo -u vagrant tee /home/vagrant/.local/bin/chef-solo << 'EOF' > /dev/null
#! /bin/sh
BUNDLE_PATH=/home/vagrant/.local/var/lib/chef-bundle BUNDLE_GEMFILE=/vagrant/chef/Gemfile BUNDLE_DISABLE_SHARED_GEMS="true" scl enable rh-ruby24 "bundler exec chef-solo $@"
EOF
	chmod +x /home/vagrant/.local/bin/*

	touch /root/.provision_install_chef
fi

yum clean all
