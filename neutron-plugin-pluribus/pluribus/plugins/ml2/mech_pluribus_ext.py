#
# COPYRIGHT 2014 Pluribus Networks Inc.
#
# All rights reserved. This copyright notice is Copyright Management
# Information under 17 USC 1202 and is included to protect this work and
# deter copyright infringement.  Removal or alteration of this Copyright
# Management Information without the express written permission from
# Pluribus Networks Inc is prohibited, and any such unauthorized removal
# or alteration will be a violation of federal law.
#

from oslo.config import cfg

from neutron import manager
from neutron.api.v2 import attributes
from neutron.common import constants as const
from neutron.openstack.common import log as logging
from neutron.plugins.ml2.drivers.mech_pluribus.mech_pluribus \
    import PluribusDriver
import threading

LOG = logging.getLogger(__name__)


class PluribusExtensionDriver(PluribusDriver):

    """Ml2 Extension Mechanism Driver for the Pluribus Networks hardware.
    """

    def initialize(self):
        super(PluribusExtensionDriver, self).initialize()

        LOG.debug("%(module)s.%(name)s init done",
                  {'module': __name__,
                   'name': self.__class__.__name__})

    def create_subnet_postcommit(self, context):
        """For this model this method will be delegated to vswitch plugin."""
        LOG.debug(('Pluribus create_subnet_postcommit() called:',
                   context.current))
        subnet = context.current
        # check if the pn_dhcp is set to true and the subnet
        # is also marked to use dhcp service
        if cfg.CONF.PLURIBUS_PLUGINS[
                'pn_dhcp'] and subnet['enable_dhcp']:
            # add a key to tell the pn switch that we need dhcp
            subnet['pn_dhcp'] = True
            LOG.debug(("subnet['pn_dhcp'] = True"))

        # get the network information
        core_plugin = manager.NeutronManager.get_plugin()
        net = core_plugin.get_network(context._plugin_context,
                                      subnet['network_id'])

        LOG.debug(('create_subnet_postcommit , net status :', net['status']))

        port = self.create_subnet_port(context, subnet)

        if net['status'] == const.NET_STATUS_BUILD:
            # fork async
            async_thread = threading.Thread(
                name='create_subnet_impl',
                target=self.create_subnet_impl,
                args=(context, subnet, net, port,)
            )
            async_thread.daemon = True
            async_thread.start()
        else:
            self.create_subnet_impl(context, subnet, net, port)

        return subnet

    def create_subnet_port(self, context, subnet):
        LOG.debug(('Pluribus Driver create_subnet_port '))

        core_plugin = manager.NeutronManager.get_plugin()

        net = {'id': subnet['network_id']}

        try:
            LOG.debug(('get_network_ext'))
            net_ext = self.server.get_network_ext(**net)
            LOG.debug(('get_network_ext : ', net_ext))
        except Exception as e:
            LOG.debug(('create_subnet failed, rolling back'))
            raise e

        # create a new port for dhcp endpoint on the switch if it is not marked
        # as 'external network'.
        # for an 'external network' we use the gateway ip information which is
        # provided by admin during network create - the assumption is that the
        # gateway IP is within the openstack infrastructure and not outside it
        if 'default_gw' in net_ext and \
                net_ext['default_gw'] == 'True':
            LOG.debug(('create_subnet_port : setting default gw'))
            dhcp_port = {
                'fixed_ips': [
                    {
                        'subnet_id': subnet['id'],
                        'ip_address': subnet['gateway_ip']
                    }
                ]
            }
        else:
            fixed_ip = {'subnet_id': subnet['id']}
            port_name = subnet['name'] + '-dhcp'
            port_data = {
                'tenant_id': subnet['tenant_id'],
                'name': port_name,
                'network_id': subnet['network_id'],
                'mac_address': attributes.ATTR_NOT_SPECIFIED,
                'admin_state_up': True,
                'device_id': '',
                'device_owner': const.DEVICE_OWNER_DHCP,
                'fixed_ips': [fixed_ip]
            }

            # create a port for dhcp
            dhcp_port = core_plugin.create_port(context._plugin_context,
                                                {'port': port_data})

        return dhcp_port
