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

import logging

from neutron import manager
from neutron.api.v2 import attributes
from neutron.common import constants as const
from neutron.db import db_base_plugin_v2
from neutron.db import extraroute_db
from neutron.db import l3_gwmode_db
from neutron.db import l3_db
from neutron.openstack.common import importutils
from neutron.plugins.common import constants

LOG = logging.getLogger(__name__)


class PluribusRouterPlugin(db_base_plugin_v2.NeutronDbPluginV2,
                           db_base_plugin_v2.CommonDbMixin,
                           extraroute_db.ExtraRoute_db_mixin,
                           l3_gwmode_db.L3_NAT_db_mixin):

    """Implementation of the Pluribus Networks L3 Router Service Plugin.
    This class implements all Openstack controller- PN switch interactions
    related to L3 routing.
    """

    supported_extension_aliases = ["router"]

    def __init__(self):

        super(PluribusRouterPlugin, self).__init__()
        self.server = importutils.\
            import_object(cfg.CONF.PLURIBUS_PLUGINS['pn_api'])

    @property
    def core_plugin(self):
        return manager.NeutronManager.get_plugin()

    def get_plugin_type(self):
        return constants.L3_ROUTER_NAT

    def get_plugin_description(self):
        """Returns string description of the plugin"""
        return ("Pluribus Networks L3 Router Service plugin for"
                " basic L3 forwarding between various subnets on"
                " Openstack across multiple compute nodes or the"
                " same compute node.")

    def create_router_db(self, context, router):
        return super(PluribusRouterPlugin, self).create_router(context,
                                                               router)

    def create_router(self, context, router):
        LOG.debug(('create_router() called', router))

        r = self.create_router_db(context, router)
        try:
            self.server.create_router(**r)
        except Exception as e:
	    LOG.error("Failed to create router, rolling back")
            self.delete_router_db(context, r['id'])
            raise e

        return r

    def delete_router_db(self, context, id):
        super(PluribusRouterPlugin, self).delete_router(context, id)

    def delete_router(self, context, id):
        LOG.debug("delete_router() called")
        self.delete_router_db(context, id)
        r = {'router_id': id}
        try:
            self.server.delete_router(**r)
        except Exception as e:
	    LOG.error("Failed to delete router")
            raise e

    def update_router(self, context, id, router):
        LOG.debug(("update_router() called: {} {}", id, router))

        ext_gw_subnet_info = None
        if self.router_has_external_gateway(context, id):
            ext_gw_subnet_info = self.get_router_external_subnet_info(context,
                                                                      id)

        updt_router = super(PluribusRouterPlugin, self).\
            update_router(context, id, router)

        LOG.debug(("updated_router = ", updt_router))

        if updt_router['external_gateway_info'] is not None:

            # get the external subnet id
            device_filter = {'device_id': [id],
                             'device_owner': ["network:router_gateway"]}
            # TODO: change the self call
            ext_port_list = self.get_ports(context, filters=device_filter)
            LOG.debug(('external port = ', ext_port_list))
            ext_port = ext_port_list[0]
            ext_subnet_id = ext_port['fixed_ips'][0]['subnet_id']

            updt_router['external_port'] = []

            # assign a IP address
            # TODO: change the self call
            ports = self.create_port_on_external_network(context, id,
                                                         updt_router['name'])
            LOG.debug(('port router_gateway ', ports))
            LOG.debug(('port for network ', ports['network_id']))
            LOG.debug(('port = ', ports['fixed_ips'][0]['ip_address']))

            port_info = {'network_id': ports['network_id'],
                         'port': ports}
            updt_router['external_port'].append(port_info)
            ext_port['status'] = const.PORT_STATUS_ACTIVE
            port_info = {}
            port_info['port'] = ext_port
            self.update_port(context, ext_port['id'], port_info)
        else:
            LOG.debug(('setting external gateway to None'))

            if ext_gw_subnet_info is not None:
                # TODO: change the self call
                all_ports = self.get_ports(context)

                # remove the port
                port_name = ext_gw_subnet_info['name'] + id
                self.delete_ports_with_name(context, all_ports, port_name)
                updt_router['external_gw_cidr'] = ext_gw_subnet_info['cidr']

        self.server.update_router(**updt_router)

        return updt_router

    def add_router_interface_db(self, context, router_id, interface_info):
        return super(PluribusRouterPlugin, self).\
            add_router_interface(context, router_id, interface_info)

    def _get_router_info(self, context, router_id, interface_info):
        interface_ip = None
        use_specific_ip = None

        if 'subnet_id' in interface_info:
            # get the subnet information and the network it belongs to
            sbn = self.get_subnet(context, interface_info['subnet_id'])

            LOG.debug(("subnet = {}", sbn))
            network_id = sbn['network_id']
            subnet_id = sbn['id']
            cidr = sbn['cidr']

            if not sbn['gateway_ip']:
                fixed_ip = {'subnet_id': sbn['id']}
                port_name = sbn['name'] + router_id
                port_data = {
                    'tenant_id': sbn['tenant_id'],
                    'name': port_name,
                    'network_id': sbn['network_id'],
                    'mac_address': attributes.ATTR_NOT_SPECIFIED,
                    'admin_state_up': False,
                    'device_id': '',
                    'device_owner': '',
                    'fixed_ips': [fixed_ip]
                }

                ports = self.core_plugin.create_port(context,
                                                     {'port': port_data})

                interface_ip = ports['fixed_ips'][0]['ip_address']

            else:
                interface_ip = sbn['gateway_ip']
        elif 'port_id' in interface_info:
            pfilter = {'id': [interface_info['port_id']]}
            port = self.get_ports(context, filters=pfilter)
            network_id = port[0]['network_id']
            subnet_id = port[0]['fixed_ips'][0]['subnet_id']
            sbn = self.get_subnet(context, subnet_id)
            cidr = sbn['cidr']
            interface_ip = port[0]['fixed_ips'][0]['ip_address']
            use_specific_ip = True

        router = {'network_id': network_id,
                  'router_id': router_id,
                  'cidr': cidr,
                  'subnet_id': subnet_id,
                  'interface_ip': interface_ip}
        if use_specific_ip:
            router['use_specific_ip'] = use_specific_ip

        return router

    def add_router_interface(self, context, router_id, interface_info):
        LOG.debug(("add_router_interface() called", interface_info))

        info = self.add_router_interface_db(context, router_id, interface_info)
        router = self._get_router_info(context, router_id, interface_info)

        try:
            self.server.plug_router_interface(**router)
        except Exception as e:
            LOG.debug(('add router interface failed, rolling back'))
            super(PluribusRouterPlugin, self).\
                remove_router_interface(context, router_id, interface_info)

            raise e

        # update the port state once the vrouter create has succeeded
        self.set_port_status_active(context, router_id, router['subnet_id'])

        return info

    def set_port_status_active(self, context, router_id, subnet_id):
        device_filter = {'device_id': [router_id]}
        router_ports = self.get_ports(context, filters=device_filter)
        for p in router_ports:
            fa = p['fixed_ips']
            for addr in fa:
                if addr['subnet_id'] == subnet_id:
                    p['status'] = const.PORT_STATUS_ACTIVE
                    port_info = {}
                    port_info['port'] = p
                    self.core_plugin.update_port(context, p['id'], port_info)
                    break

    def remove_router_interface_db(self, context, router_id, interface_info):
        super(PluribusRouterPlugin, self).remove_router_interface(
            context, router_id, interface_info)

    def remove_router_interface(self, context, router_id, interface_info):
        LOG.debug(("remove_router_interface() called"))

        if 'subnet_id' not in interface_info:
            if 'port_id' not in interface_info:
                LOG.debug(('either port_id or subnet_id needs to be present'))
                return

            pfilter = {'id': [interface_info['port_id']]}
            port = self.get_ports(context, filters=pfilter)
            if port is None:
                LOG.debug(("remove router interface, unable to find port"))
                return

            subnet_id = port[0]['fixed_ips'][0]['subnet_id']
        else:
            subnet_id = interface_info['subnet_id']

        self.remove_router_interface_db(context, router_id, interface_info)
        subnet = self.get_subnet(context, subnet_id)

        router = {'network_id': subnet['network_id'],
                  'router_id': router_id,
                  'subnet_id': subnet_id,
                  'cidr': subnet['cidr']}

        # delete the gateway ip which might have been created
        if not subnet['gateway_ip']:
            port_name = subnet['name'] + router_id
            ports = self.get_ports(context)
            self.delete_ports_with_name(context, ports, port_name)

        self.server.unplug_router_interface(**router)

    def get_external_port_info(self, context, router_id):
        LOG.debug(('get_external_port_info ', router_id))

        device_filter = {'device_id': [router_id],
                         'device_owner': ["network:router_gateway"]}
        ext_ports = self.get_ports(context, filters=device_filter)
        LOG.debug(('external port = ', ext_ports))
        return ext_ports

    def router_has_external_gateway(self, context, router_id):
        LOG.debug(('router_has_external_gateway ', router_id))

        ext_ports = self.get_external_port_info(context, router_id)
        # if there is no external gateway return
        return True if len(ext_ports) else False

    def get_router_external_subnet_info(self, context, router_id):
        LOG.debug(('get_router_external_subnet_info ', router_id))

        ext_ports = self.get_external_port_info(context, router_id)

        # get the external subnet_id
        ext_subnet_id = ext_ports[0]['fixed_ips'][0]['subnet_id']

        return self.get_subnet(context, ext_subnet_id)

    def create_port_on_external_network(self, context, router_id, name):
        LOG.debug(('create_port_on_external_network ', router_id))

        # get the network id of the external gateway
        ext_ports = self.get_external_port_info(context, router_id)
        LOG.debug(('external port = ', ext_ports))

        # get the subnet associated with the external subnet
        ext_subnet_info = self.get_router_external_subnet_info(context,
                                                               router_id)
        ext_subnet_id = ext_subnet_info['id']
        fixed_ip = {'subnet_id': ext_subnet_id}

        # the routerid can be used as the port-name
        port_name = ext_subnet_info['name'] + router_id

        # create the port data dictionary to hand to neutron
        port_data = {
            'tenant_id': ext_subnet_info['tenant_id'],
            'name': port_name,
            'network_id': ext_ports[0]['network_id'],
            'mac_address': attributes.ATTR_NOT_SPECIFIED,
            'admin_state_up': False,
            'device_id': '',
            'device_owner': '',
            'fixed_ips': [fixed_ip]
        }

        args = [context, {'port': port_data}]
        ports = self.create_port(context, {'port': port_data})

        ports['cidr'] = ext_subnet_info['cidr']

        return ports

    def delete_ports_with_name(self, context, port_list, port_name):
        LOG.debug(('delete_ports_with_name : ', port_name))
        for p in port_list:
            if port_name == p['name']:
                LOG.debug(('deleting port with name, id ', p['name'], p['id']))
                args = [context, p['id'], False]
                self.core_plugin.delete_port(context, p['id'])

    def update_port(self, context, id, port):
        """
        Perform this operation in the context of the configured device
        plugins.
        """
        LOG.debug(("update_port() called"))
        updated_port = super(PluribusRouterPlugin, self).update_port(
            context, id, port)

        LOG.debug(("updated port =", updated_port))

        self.server.update_port(**updated_port)

        return updated_port

    def create_floatingip(self, context, floatingip):
        LOG.debug(("create_floatingip {}", floatingip))
        fip = super(PluribusRouterPlugin, self).create_floatingip(context,
                                                                  floatingip)

        try:
            self.server.create_floatingip(**fip)
        except Exception as e:
            LOG.debug(('create_floating_ip failed, rolling back'))
            super(PluribusRouterPlugin, self).delete_floatingip(
                context, fip['id'])
            raise e

        return fip

    def update_floatingip(self, context, id, floatingip):
        LOG.debug(("update_floatingip {} {}", id, floatingip))
        ufip = super(PluribusRouterPlugin, self).update_floatingip(context, id,
                                                                   floatingip)
        # get the floating ip information
        LOG.debug(("floatingip = ", ufip))
        # get the port information
        if ufip['port_id'] is not None:
            subnet_id = self._get_floatingip_subnet(context, ufip)
            ufip['subnet_id'] = subnet_id
        self.server.update_floatingip(**ufip)
        return ufip

    def delete_floatingip(self, context, id):
        LOG.debug(("delete_floatingip {}", id))

        super(PluribusRouterPlugin, self).delete_floatingip(context, id)
        fip = {'id': id}
        self.server.delete_floatingip(**fip)

    def _get_floatingip_subnet(self, context, fip):
        LOG.debug(("get_floatingip_subnet ", fip))
        pfilter = {'id': [fip['port_id']]}
        ports = self.get_ports(context, filters=pfilter)
        fixed_ip_list = ports[0]['fixed_ips']
        for f in fixed_ip_list:
            if fip['fixed_ip_address'] == f['ip_address']:
                return f['subnet_id']
        return None

    def disassociate_floatingips(self, context, port_id, do_notify=True):
        # determing the floating IP's id using port_id
        floating_ip_ids = []
        with context.session.begin(subtransactions=True):
            floating_ip = (context.session.query(l3_db.FloatingIP).
                           filter_by(fixed_port_id=port_id))
            for entry in floating_ip:
                floating_ip_ids.append(entry['id'])
                LOG.debug(("disassociate_floatingips {}", port_id))
                super(PluribusRouterPlugin, self).disassociate_floatingips(
                    context, port_id, do_notify)
                fid = {'id': floating_ip_ids}
                self.server.disassociate_floatingips(**fid)
