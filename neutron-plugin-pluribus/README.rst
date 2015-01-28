OpenStack Neutron Pluribus Plugin
======

1. Introduction
------
Pluribus Networks (http://www.pluribusnetworks.com) was founded in April 2010 by Sunay Tripathi, Robert Drost, and C.K. Ken Yang to deliver server economics, innovation, and programmability to top of the rack switching. With over 50 years of experience and more than 200 patents collectively, the founders brought hard-core expertise in network operating systems, virtualization, and high-performance hardware-software integration. Using Sunay's background in network virtualization and kernel development, Robert's background in proximity communication, and Ken's authority on high speed serial links, the founding team had all the ingredients needed to tightly integrate a server and switch running a bare metal, distributed network hypervisor (Netvisor®).

OpenStack is a cloud operating system that controls large pools of compute, storage, and networking resources throughout a datacenter, all managed through a dashboard that gives administrators control while empowering their users to provision resources through a web interface.

This project hosts the Pluribus Networks plugin for OpenStack Neutron. 

2. Requirements
------
* A controller running OpenStack Havana, Icehouse or Juno
* Pluribus Networks server-switch underneath

3. Installation
------
To install the plugin:

1. Download and extract the plugin.
2. Navigate to the previously extracted directory.
3. Run:
  $ python setup.py install
4. Edit /etc/neutron/neutron.conf to set the core_plugin to the Pluribus plugin:
  core_plugin = neutron.plugins.pluribus.plugin.PluribusPlugin
5. Add the following section in /etc/neutron/neutron.conf:
  
  [PLURIBUS_PLUGINS]
  
  # The neutron core plugin that Pluribus internally uses
  
  vswitch_plugin = neutron.plugins.ml2.plugin.Ml2Plugin
  
  # The allocated VLAN range for this openstack controller from the Pluribus switch
  
  pn_vlans = 100-200
  
  # Address of the Pluribus switch agent interacting with this OpenStack controller
  
  pn_switch = 192.168.1.1
  
  # The port on which the Pluribus switch agent runs
  
  pn_port = 30000
  
6. Append the following to /etc/neutron/plugin/ml2/ml2_conf.ini:mechanism_drivers
  mechanism_drivers = pluribus.plugins.ml2.mech_pluribus.PluribusDriver
  
7. Restart the Neutron server:
  $ service neutron-server restart
