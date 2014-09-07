#!/bin/bash
#

### Log the script all outputs locally
exec > >(sudo tee install.log)
exec 2>&1

### Creat a lock to avoid running multiple instances of script.
LOCKFILE="/tmp/`basename $0`"
LOCKFD=99

# PRIVATE
_lock()             { flock -$1 $LOCKFD; }
_no_more_locking()  { _lock u; _lock xn && rm -f $LOCKFILE; }
_prepare_locking()  { eval "exec $LOCKFD>\"$LOCKFILE\""; trap _no_more_locking EXIT; }

# ON START
_prepare_locking

# PUBLIC
exlock_now()        { _lock xn; }  # obtain an exclusive lock immediately or fail

exlock_now || exit 1

### BEGIN OF SCRIPT ###
DIR=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )

### Trap any error code with related filename and line.
errtrap()
{
    FILE=${BASH_SOURCE[1]:-$BASH_SOURCE[0]}
    echo "[FILE: "$(basename $FILE)", LINE: $1] Error: Command or function exited with status $2"
}

if [[ "$-" == *x* ]]; then
trap 'errtrap $LINENO $?' ERR
fi

# Install figlet
sudo yum -y install figlet >& /dev/null
if [[ "$?" != "0" ]]; then
    echo "failed to install figlet"
    exit 1
else
    echo "figlet is installed"
fi
figlet -ctf slant Compass Metrics Installer

while [ $1 ]; do
  flags=$1
  param=${flags/'--'/''}
  var=$(echo $param | cut -d"=" -f1)
  val=$(echo $param | cut -d"=" -f2)
  export $var=$val
  shift
done

# Load variables
loadvars()
{
    varname=${1,,}
    eval var=\$$(echo $1)

    if [[ -z $var ]]; then
        echo -e "\x1b[32mPlease enter the $varname (Example: $2):\x1b[37m"
        while read input
        do
            if [ "$input" == "" ]; then
                echo "Default $varname '$2' chosen"
                export $(echo $1)="$2"
                break
            else
                echo "You have entered $input"
                export $(echo $1)="$input"
                break
            fi
        done
    fi
}

loadvars NIC "eth0"
sudo ifconfig $NIC
if [ $? -ne 0 ]; then
    echo "There is no nic '$NIC' yet"
    exit 1
fi
sudo ifconfig $NIC | grep 'inet addr:' >& /dev/null
if [ $? -ne 0 ]; then
    echo "There is not any IP address assigned to the NIC '$NIC' yet, please assign an IP address first."
    exit 1
fi

export ipaddr=$(ifconfig $NIC | grep 'inet addr:' | cut -d: -f2 | awk '{ print $1}')

export SCRIPT_DIR=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )
export COMPASS_METTRICS_DIR=${SCRIPT_DIR}/..

echo 'Installing Required packages for Compass monit...'
sudo yum clean all
sudo yum update -y --skip-broken

sudo yum install -y python python-devel git wget syslinux mod_wsgi httpd yum-utils python-virtualenv
if [[ "$?" != "0" ]]; then
    echo "failed to install yum dependency"
    exit 1
fi

sudo easy_install --upgrade pip
if [[ "$?" != "0" ]]; then
    echo "failed to install easy install"
    exit 1
fi

sudo pip install virtualenvwrapper

sudo chkconfig httpd on

sudo mkdir -p /var/www/compass_monit
sudo mkdir -p /var/log/compass_monit
sudo mkdir -p /etc/compass_monit
sudo 
sudo chmod -R 777 /var/log/compass_monit


cp -rf ${COMPASS_METTRICS_DIR}/conf/compass-monit.conf /etc/httpd/conf.d/compass-monit.conf
sudo cp -rf ${COMPASS_METTRICS_DIR}/conf/compass_monit.wsgi /var/www/compass_monit/compass_monit.wsgi
sudo cp -rf ${COMPASS_METTRICS_DIR}/conf/setting /etc/compass_monit/setting

cd ${COMPASS_METTRICS_DIR}
source `which virtualenvwrapper.sh`
if ! lsvirtualenv |grep compass-monit>/dev/null; then
    mkvirtualenv compass-monit
fi
workon compass-monit
python setup.py install
if [[ "$?" != "0" ]]; then
    echo "failed to install compass-monit package"
    deactivate
    exit 1
else
    echo "compass-monit package is installed in virtualenv under current dir"
fi

sudo sed -e 's|$PythonHome|'$VIRTUAL_ENV'|' -i /var/www/compass_monit/compass_monit.wsgi
sudo sed -i "s/\$ipaddr/$ipaddr/g" /etc/compass_monit/setting

deactivate

sudo service httpd restart
sleep 10
sudo service httpd status
if [[ "$?" != "0" ]]; then
    echo "httpd is not started"
    exit 1
else
    echo "httpd has already started"
fi

figlet -ctf slant Installation Complete!
echo -e "It takes\x1b[32m $SECONDS \x1b[0mseconds during the installation."
