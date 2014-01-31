Summary: yamabiko
Name: yamabiko
Version: 1.1.18
License: APL2
Release: 1%{?dist}

Group: System Environment/Daemons
Vendor: Y-Ken Studio
URL: https://github.com/y-ken/yamabiko
Source: %{name}-%{version}.tar.gz
Source1: %{name}.init
BuildRoot: %{_tmppath}/%{name}-%{version}-%{release}-%(%{__id_u} -n)

Requires: /usr/sbin/useradd /usr/sbin/groupadd
Requires: /sbin/chkconfig
Requires: openssl readline libxslt libxml2 yamabiko-libyaml
Requires(pre): shadow-utils
Requires(post): /sbin/chkconfig
Requires(post): /sbin/service
Requires(preun): /sbin/chkconfig
Requires(preun): /sbin/service
BuildRequires: gcc gcc-c++ pkgconfig libtool openssl-devel readline-devel libxslt-devel libxml2-devel libyaml-devel

# 2011/08/01 Kazuki Ohta <kazuki.ohta@gmail.com>
# prevent stripping the debug info.
%define debug_package %{nil}
%define __strip /bin/true

%description

%prep
# check mysql-devel is installed
if [ -z "`which mysql_config`" ]
then
  echo 'Requires: mysql-devel or MySQL-devel'
  exit 1
fi

%setup -q

%build
./autogen.sh

%configure
make %{?_smp_mflags}

%install
# cleanup first
rm -rf $RPM_BUILD_ROOT
# install programs
make install DESTDIR=$RPM_BUILD_ROOT INSTALL="install -p"
# install init.d script
mkdir -p $RPM_BUILD_ROOT/etc/init.d/
install -m 755 %{S:1} $RPM_BUILD_ROOT/etc/init.d/%{name}
# create log dir
mkdir -p $RPM_BUILD_ROOT/var/log/%{name}
# Grep reports BUILDROOT inside our object files; disable that test.
QA_SKIP_BUILD_ROOT=1
export QA_SKIP_BUILD_ROOT

%clean
rm -rf $RPM_BUILD_ROOT

%post
echo "adding 'yamabiko' group..."
getent group yamabiko >/dev/null || /usr/sbin/groupadd -r yamabiko
echo "adding 'yamabiko' user..."
getent passwd yamabiko >/dev/null || \
  /usr/sbin/useradd -r -g yamabiko -d %{_localstatedir}/lib/yamabiko -s /sbin/nologin -c 'yamabiko' yamabiko
chown -R yamabiko:yamabiko /var/log/%{name}
if [ ! -e "/etc/yamabiko/yamabiko.conf" ]; then
  echo "Installing default conffile $CONFFILE ..."
  cp -f /etc/yamabiko/yamabiko.conf.tmpl /etc/yamabiko/yamabiko.conf
fi

# 2011/11/13 Kazuki Ohta <k@treasure-data.com>
# This prevents prelink, to break the Ruby intepreter.
if [ -d "/etc/prelink.conf.d/" ]; then
  echo "prelink detected. Installing /etc/prelink.conf.d/yamabiko-ruby.conf ..."
  cp -f /etc/yamabiko/prelink.conf.d/yamabiko.conf /etc/prelink.conf.d/yamabiko-ruby.conf
elif [ -f "/etc/prelink.conf" ]; then
  if [ $(grep '\-b /usr/lib{,64}/yamabiko/ruby/bin/ruby' -c /etc/prelink.conf) -eq 0 ]; then
    echo "prelink detected, but /etc/prelink.conf.d/ dosen't exist. Adding /etc/prelink.conf ..."
    echo "-b /usr/lib{,64}/yamabiko/ruby/bin/ruby" >> /etc/prelink.conf
  fi
fi

# 2013/03/04 Kazuki Ohta <k@treasure-data.com>
# Install log rotation script.
if [ -d "/etc/logrotate.d/" ]; then
  cp -f /etc/yamabiko/logrotate.d/yamabiko.logrotate /etc/logrotate.d/yamabiko
fi

# 2011/11/13 Kazuki Ohta <k@treasure-data.com>
# Before yamabiko v1.1.0, fluentd has a bug of loading plugin before changing
# to the right user. Then, these directories were created with root permission.
# The following lines fix that problem.
if [ -d "/var/log/yamabiko/buffer/" ]; then
  chown -R yamabiko:yamabiko /var/log/yamabiko/buffer/
fi
if [ -d "/tmp/yamabiko/" ]; then
  chown -R yamabiko:yamabiko /tmp/yamabiko/
fi

echo "install fluent-plugin-mysql-replicator..."
GEMPATH=/usr/lib*/yamabiko/ruby/bin/gem
$GEMPATH install --no-rdoc --no-ri fluent-plugin-mysql-replicator

echo "Configure yamabiko to start, when booting up the OS..."
/sbin/chkconfig --add yamabiko

# 2011/03/24 Kazuki Ohta <k@treasure-data.com>
# When upgrade, restart agent if it's launched
if [ "$1" = "2" ]; then
  /sbin/service yamabiko condrestart >/dev/null 2>&1 || :
fi

%preun
# 2011/02/21 Kazuki Ohta <k@treasure-data.com>
# Just leave this file, because this line could delete yamabiko.conf in a
# *UPGRADE* process :-(
# if [ -e "/etc/prelink.conf.d/yamabiko-ruby.conf" ]; then
#   echo "Uninstalling /etc/prelink.conf.d/yamabiko-ruby.conf ..."
#   rm -f /etc/prelink.conf.d/yamabiko-ruby.conf
# fi
if [ $1 = 0 ] ; then
  echo "Stopping yamabiko ..."
  /sbin/service yamabiko stop >/dev/null 2>&1 || :
  /sbin/chkconfig --del yamabiko
fi

%files
%defattr(-,root,root)
/usr/sbin/yamabiko
/usr/%{_lib}/yamabiko
/etc/yamabiko
/etc/init.d/yamabiko
/var/log/yamabiko

%changelog
* Thu Dec 5 2013 Masahiro Nakagawa <masa@treasure-data.com>
- v1.1.18
- ruby v1.9.3-p484 (security fix)
- fluentd v0.10.41
- td-client v0.8.56
- td v0.10.96
- fluent-plugin-s3 v0.3.5
- fluent-plugin-td v0.10.17
- fluent-plugin-rewrite-tag-filter v1.3.1
- fluent-plugin-td-monitoring v0.1.0

* Wed Sep 25 2013 Masahiro Nakagawa <masa@treasure-data.com>
- v1.1.17
- fluentd v0.10.39
- td-client v0.8.55
- td v0.10.89
- fluent-plugin-td v0.10.16
- Fix configtest permission issue at restart

* Fri Aug 30 2013 Masahiro Nakagawa <masa@treasure-data.com>
- v.1.1.16
- fluentd v0.10.38
- td-client v0.8.54
- td v0.10.86
- Add configtest and use configtest at restart

* Thu Aug 2 2013 Masahiro Nakagawa <masa@treasure-data.com>
- v.1.1.15
- fluentd v0.10.36
- td-client v0.8.53
- td v0.10.84
- fluent-plugin-s3 v0.3.4
- fluent-plugin-webhdfs v0.2.1
- fluent-plugin-mongo v0.7.1
- cool.io v1.1.1

* Thu Jun 20 2013 Masahiro Nakagawa <masa@treasure-data.com>
- v.1.1.14
- fluentd v0.10.35
- td-client v0.8.52
- td v0.10.82
- fluent-plugin-s3 v0.3.3
- fluent-plugin-webhdfs v0.2.0
- webhdfs v0.5.3
- bson_ext v1.8.6
- bson v1.8.6
- mongo v1.8.6
- yajl-ruby v1.1.0
- json v1.7.7

* Thu Apr 22 2013 Kazuki Ohta <k@treasure-data.com>
- v.1.1.13
- fluent-plugin-td v0.10.14
- td-client v0.8.48
- td v0.10.76

* Thu Mar 28 2013 Kazuki Ohta <k@treasure-data.com>
- v1.1.12
- fluentd v0.10.33
- fluent-plugin-s3 v0.3.1
- fluent-plugin-td v0.10.13
- fluent-plugin-mongo v0.7.0
- fluent-plugin-webhdfs v0.1.2
- msgpack v0.4.7
- bson_ext v1.8.4
- bson v1.8.4
- mongo v1.8.4
- iobuffer v1.1.2

* Thu Dec 06 2012 Kazuki Ohta <k@treasure-data.com>
- v1.1.11
- fluentd v0.10.30
- fluent-plugin-s3 v0.2.5
- fluent-plugin-td v0.10.13
- fluent-plugin-mongo v0.6.11

* Tue Oct 16 2012 Kazuki Ohta <k@treasure-data.com>
- v1.1.10.3
- td-client v0.8.34

* Mon Oct 15 2012 Kazuki Ohta <k@treasure-data.com>
- v1.1.10.2
- fluent-plugin-td v0.10.12

* Mon Oct 15 2012 Kazuki Ohta <k@treasure-data.com>
- v1.1.10.1
- fix /usr/bin/td error of setting GEM_HOME and GEM_PATH

* Mon Oct 15 2012 Kazuki Ohta <k@treasure-data.com>
- v1.1.10
- fluentd v0.10.27
- fluent-plugin-mongo v0.6.9
- fluent-plugin-webhdfs v0.5.1
- fluent-plugin-td v0.10.11
- enable debug agent by default (td-agent.conf)
- set GEM_HOME and GEM_PATH at /usr/[s]bin/scripts to avoid RVM conflicts

* Mon Aug 27 2012 Kazuki Ohta <k@treasure-data.com>
- v1.1.9
- fix problem of /usr/bin/td, which doesn't take any cmd arguments

* Mon Jul 23 2012 Kazuki Ohta <k@treasure-data.com>
- v1.1.8
- fluentd v0.10.25
- fix critical problem of duplicate daemon launching

* Mon Jun 11 2012 Kazuki Ohta <k@treasure-data.com>
- v1.1.7
- bson_ext v1.6.4
- bson v1.6.4
- mongo v1.6.4
- fluent-plugin-td v0.10.7
- td v0.10.25 (new)
- install /usr/bin/td (new)

* Sun May 20 2012 Kazuki Ohta <k@treasure-data.com>
- v1.1.6
- remove ruby package dependency
- fluent-plugn-flume v0.1.1 (new)

* Wed May 02 2012 Kazuki Ohta <k@treasure-data.com>
- v1.1.5.1
- fluentd v0.10.22

* Tue May 01 2012 Kazuki Ohta <k@treasure-data.com>
- v1.1.5
- ruby v1.9.3-p194 (security fix)
- fluentd v0.10.21
- add --with-libyaml-dir to ruby's configure options

* Mon Apr 23 2012 Kazuki Ohta <k@treasure-data.com>
- v1.1.4.4
- depends on td-libyaml for both RHEL5 and RHEL6

* Sat Apr 17 2012 Kazuki Ohta <k@treasure-data.com>
- v1.1.4
- use ruby-1.9.3-p125
- use jemalloc v2.2.5, to avoid memory fragmentations
- fluentd v0.10.19
- fluent-plugin-mongo v0.6.7
- fluent-plugin-td v0.10.6

* Sat Mar 25 2012 Kazuki Ohta <k@treasure-data.com>
- v1.1.3.1
- fix not to start td-agent daemon, when installing. thx @moriyoshi.
- various fix for CentOS 4 (prelink & status). thx @riywo.

* Sun Mar 10 2012 Kazuki Ohta <k@treasure-data.com>
- v1.1.3
- fluent-plugin-mongo v0.6.6

* Wed Feb 22 2012 Kazuki Ohta <k@treasure-data.com>
- v1.1.2.2
- fix package dependency

* Tue Feb 21 2012 Kazuki Ohta <k@treasure-data.com>
- v1.1.2.1
- fix not to remove prelink file, when updating the package

* Wed Feb 08 2012 Kazuki Ohta <k@treasure-data.com>
- v1.1.2
- fluentd v0.10.10
- fluent-plugin-td v0.10.5
- fluent-plugin-scribe v0.10.7
- fluent-plugin-mongo v0.6.3

* Mon Jan 23 2012 Kazuki Ohta <k@treasure-data.com>
- fluentd v0.10.9
- fluent-plugin-scribe v0.10.6
- fluent-plugin-mongo v0.6.2
- fluent-plugin-s3 v0.2.2 (new)
- fix /var/run/td-agent/ creation in init.d script
- fix Ruby interpreter breakinb by prelink, on 32-bit platform

* Fri Nov 11 2011 Kazuki Ohta <k@treasure-data.com>
- fluentd v0.10.6
- fluent-plugin-td v0.10.2
- fluent-plugin-scribe v0.10.3
- fluent-plugin-mongo v0.4.0 (new)
- prevent Ruby interpreter breaking by prelink

* Mon Oct 10 2011 Kazuki Ohta <k@treasure-data.com>
- fix gem installation order

* Mon Oct 05 2011 Kazuki Ohta <k@treasure-data.com>
- fix posinst

* Mon Oct 01 2011 Kazuki Ohta <k@treasure-data.com>
- fluent v0.9.16
- fluent-plugin-scribe v0.9.10

* Mon Sep 20 2011 Kazuki Ohta <k@treasure-data.com>
- fluent v0.9.14
- fluent-plugin-td v0.9.10

* Mon Sep 20 2011 Kazuki Ohta <k@treasure-data.com>
- fluent v0.9.13

* Mon Sep 16 2011 Kazuki Ohta <k@treasure-data.com>
- fluent v0.9.10
- fluent-plugin-scribe v0.9.8

* Mon Sep 05 2011 Kazuki Ohta <k@treasure-data.com>
- fluent v0.9.9
- add fluent-plugin-scribe gem

* Sun Aug 18 2011 Kazuki Ohta <k@treasure-data.com>
- fluent v0.9.8

* Sun Aug 07 2011 Kazuki Ohta <k@treasure-data.com>
- fix calling undefined function in daemon mode

* Sun Aug 07 2011 Kazuki Ohta <k@treasure-data.com>
- fluent v0.9.7, with fluent-plugin-td gem

* Mon Aug 01 2011 Kazuki Ohta <k@treasure-data.com>
- fluent v0.9.5. initial packaging for Scientific Linux 6
