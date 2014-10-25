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
export SCRIPT_DIR=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )
export COMPASS_METTRICS_DIR=${SCRIPT_DIR}/..


if [ ! -f "/etc/yum.repos.d/datastax.repo" ]; then
    cp -rf ${COMPASS_METTRICS_DIR}/conf/datastax.repo /etc/yum.repos.d/datastax.repo
fi

if [ ! -f "/etc/yum.repos.d/datastax.repo" ]; then
    echo "cannot find datastax repo"
    exit 1
fi


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
loadvars KAIROSDB_PORT "8088"
loadvars COMPASS_NODE_IP "10.145.89.1"
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

echo 'Installing Required packages for Compass monit...'
sudo yum clean all
sudo yum update -y --skip-broken

sudo yum install -y python python-devel git wget syslinux mod_wsgi httpd yum-utils python-virtualenv java-1.7.0-openjdk dsc20
if [[ "$?" != "0" ]]; then
    echo "failed to install yum dependency"
    exit 1
fi

sudo rpm -q kairosdb
if [[ "$?" != "0" ]]; then
    #sudo rpm -Uvh http://dl.bintray.com/brianhks/generic/kairosdb-0.9.3-2.rpm
    sudo rpm -Uvh https://github.com/kairosdb/kairosdb/releases/download/v0.9.4/kairosdb-0.9.4-6.rpm
    if [[ "$?" != "0" ]]; then
	echo "failed to install kairosdb"
	exit 1
    else:
        echo "successfully installed kairosdb"
    fi
fi

cp -rf ${COMPASS_METTRICS_DIR}/conf/kairos-carbon-1.0.jar /opt/kairosdb/lib/
cp -rf ${COMPASS_METTRICS_DIR}/conf/kairosdb.properties /opt/kairosdb/conf/kairosdb.properties

sudo easy_install --upgrade pip
if [[ "$?" != "0" ]]; then
    echo "failed to install easy install"
    exit 1
fi

sudo pip install virtualenvwrapper
if [[ "$?" != "0" ]]; then
    echo "failed to install pip dependency"
    exit 1
fi

sudo chkconfig httpd on

sudo mkdir -p /var/www/compass_monit
sudo mkdir -p /var/log/compass_monit
sudo mkdir -p /etc/compass_monit
sudo chmod -R 777 /etc/compass_monit
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

## NOTE: This will code change if chef installs this piece
#  We will have to support monitor node install seperate from compass
#  For now these variable are included for that purpose and testing
#
sudo sed -e 's|$PythonHome|'$VIRTUAL_ENV'|' -i /var/www/compass_monit/compass_monit.wsgi
sudo sed -i "s/\$ipaddr/$ipaddr/g" /etc/compass_monit/setting
sudo sed -i "s/\$kairosdb_port/$KAIROSDB_PORT/g" /opt/kairosdb/conf/kairosdb.properties
sudo sed -i "s/\$kairosdb_port/$KAIROSDB_PORT/g" /etc/compass_monit/setting
sudo sed -i "s/\$compass_ipaddr/$COMPASS_NODE_IP/g" /etc/compass_monit/setting

deactivate

sudo service kairosdb stop

sudo service cassandra restart
sudo service cassandra status
if [[ "$?" != "0" ]]; then
    echo "cassandra is not started"
    exit 1
else
    echo "cassandra has already started"
fi

sudo /opt/kairosdb/bin/kairosdb-service.sh restart
if [[ "$?" != "0" ]]; then
    echo "kairosdb is not started"
    exit 1
else
    echo "kairosdb has already started"
fi

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
