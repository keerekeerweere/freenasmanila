===================================
OpenStack Manila driver for FreeNAS
===================================
Manila is the name of project which provides ‘Shared file system Service’ for OpenStack. The source code in this directory represents manila driver implementation for FreeNAS, where FreeNAS is Free and Open Source Network Attached Storage(NAS) software appliance. The driver code here is FreeNAS specific only and hence can not work with other storage appliances. This implementation supports NFS protocol, other protocols like CIFS etc.

Files
-----
* process_req.py - This is request processor, this helps processing requests from OpenStack and preparing corresponding FreeNAS REST API’s .
* driver.py - This is main driver file which provides support for primary routines called by OpenStack 
* freenasapi.py - This file provides REST based API interfaces for FreeNAS appliance
* options.py - All configuration related stuffs are handled in this file
* utils.py - This includes supporting parsing and name generation utilities

Setup
-----
* FreeNAS server version 11.0-U2 or later
* OpenStack version Ocata or later

Installation
------------
Below are the steps user need to follow for installation on OpenStack or Devstack Setup-

* Put this folder at manila driver path (e.g. /opt/stack/manila/manila/share/drivers/ )
* Edit the /etc/manila/manila.conf file as described in “Configuration section” below.
* Restart manila services.

On the FreeNAS side user need to create top level zfs pool with name ‘agattivol’. All the shares created using this driver will be placed under ‘agattivol’ pool.

TODO
----
* Implementation of access permissions
* Other Protocols support like CIFS etc. 
* Unit tests for FreeNAS manila driver

Configuration
-------------
User need to edit /etc/manila/manila.conf file as per their own setup details.

* In the [DEFAULT] section add/edit following line-
        enabled_share_backends = <name of the manila driver implemented> (  e.g. freenas )

* Add following section in the manila.conf file-

        [freenas]
                share_driver = manila.share.drivers.freenas.driver.FreeNasDriver 
                freenas_server_hostname = <IP address of FreeNAS appliance> 
                freenas_login = <username for login to FreeNAS appliance> 
                freenas_password = <Password of above user for FreeNAS appliance> 
                share_backend_name = <Name of the backend vendor> e.g. freenas
                driver_handles_share_servers = False

Note
----
In case any difficulties please feel free to reachout us-

Ram Suradkar <ram@agattilabs.com>,

Jitendra Pawar <jitendra@agattilabs.com> OR info@agattilabs.com
