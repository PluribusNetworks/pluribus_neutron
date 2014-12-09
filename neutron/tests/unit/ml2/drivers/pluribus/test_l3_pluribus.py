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

import mock
from mock import PropertyMock

from neutron.services.l3_router.l3_pluribus import PluribusRouterPlugin
from neutron.tests import base
from oslo.config import cfg
from oslo.utils.importutils import import_object


class Router(object):

    router_id = 'router-1'
    router_name = 'r1'
    gw_port_id = None
    external_gateway_info = None
    admin_state_up = True
    status = 'ACTIVE'


class FloatingIP(object):
    floating_net_id = 'extnet-1'
    floating_id = 'float-1'
    floating_ip_addr = '192.168.9.3'
    fixed_ip_address = None


class Subnet(object):

    subnet_id = 'subnet-1'
    subnet_name = 's1'
    cidr = '150.0.0.0/24'
    gateway_ip = '150.0.0.1'
    ip_version = 4
    allocation_pools = [{'start': '150.0.0.2', 'end': '150.0.0.254'}]


class Network(object):

    network_id = 'network-1'
    network_name = 'n1'


class Port(object):

    port_id = 'port-1'
    port_name = 'p1'
    ip_address = '150.0.0.2'


class FakeContext(object):

    def __init__(self):
        pass


class PluribusRouterTestCase(base.BaseTestCase,
                             Router,
                             Subnet,
                             Network,
                             Port,
                             FloatingIP):

    """Test Case for Pluribus Router service plugin."""

    @mock.patch('oslo.utils.importutils.import_object')
    def setUp(self, mock_server):
        super(PluribusRouterTestCase, self).setUp()
        self.service = PluribusRouterPlugin()
        self.service.server = mock_server
        self.tenant_id = 'tenant-1'
        self.context = FakeContext()
        setattr(cfg.CONF, 'core_plugin', 'neutron.plugins.ml2.plugin.Ml2Plugin')

    def _get_router_dict(self):
        router = {
            'name': self.router_name,
            'gw_port_id': self.gw_port_id,
            'external_gateway_info': self.external_gateway_info
        }

        return router

    def _get_server_router_dict(self):
        router = self._get_router_dict()
        router.update(
            {
                'id': self.router_id,
                'admin_state_up': self.admin_state_up,
                'status': self.status
            }
        )

        return router

    def _get_floatingip_dict(self, fixed=False):
        self.fixed_ip_address = self.ip_address if fixed else None
        self.port_id = 'port-1' if fixed else None
        fip = {
            'floating_network_id': self.floating_net_id,
            'fixed_ip_address': self.fixed_ip_address,
            'port_id': self.port_id
        }

        return fip

    def _get_floatingip_dict_server(self, fixed=False):
        self.router_id = 'router-1' if fixed else None
        fip = self._get_floatingip_dict(fixed)
        fip['floating_ip_address'] = self.floating_ip_addr
        fip['id'] = self.floating_id
        fip['status'] = self.status
        fip['router_id'] = self.router_id

        return fip

    def _get_router_interface_dict(self):
        router_intf = {
            'subnet_id': self.subnet_id
        }

        return router_intf

    def _get_subnet_info_dict(self):
        subnet_info = {
            'allocation_pools': self.allocation_pools,
            'cidr': self.cidr,
            'id': self.subnet_id,
            'name': self.subnet_name,
            'enable_dhcp': True,
            'network_id': self.network_id,
            'tenant_id': self.tenant_id,
            'gateway_ip': self.gateway_ip,
            'ip_version': self.ip_version
        }

        return subnet_info

    def _get_port_info_dict(self):
        port_info = {
            'fixed_ips': [
                {
                    'subnet_id': self.subnet_id,
                    'ip_address': self.ip_address
                }
            ],
            'id': self.port_id,
            'name': self.port_name,
            'tenant_id': self.tenant_id,
            'network_id': self.network_id
        }

        return port_info

    def test_create_router(self):
        r = self._get_router_dict()
        r_server = self._get_server_router_dict()
        with mock.patch('neutron.db.l3_db.L3_NAT_dbonly_mixin.'
                        'create_router') as create_router:
            create_router.return_value = r_server
            self.service.create_router(self.context, {'router': r})
            self.service.server.create_router.assert_called_once_with(
                name=self.router_name,
                gw_port_id=self.gw_port_id,
                external_gateway_info=self.external_gateway_info,
                id=self.router_id,
                admin_state_up=self.admin_state_up,
                status=self.status
            )

    def test_delete_router(self):
        r = {'router_id': self.router_id}
        with mock.patch('neutron.db.l3_db.L3_NAT_db_mixin.'
                        'delete_router') as delete_router:
            self.service.delete_router(self.context, self.router_id)
            self.service.server.delete_router.assert_called_once_with(
                router_id=self.router_id
            )

    @mock.patch('neutron.plugins.ml2.plugin.Ml2Plugin')
    def test_add_router_interface(self, mock_ml2):
        r_intf = self._get_router_interface_dict()

        with mock.patch('neutron.db.l3_db.L3_NAT_db_mixin.'
                        'add_router_interface') as add_intf:
            with mock.patch('neutron.services.l3_router.l3_pluribus.PluribusRouterPlugin.core_plugin', new_callable=PropertyMock) as mock_core_plugin:
                mock_core_plugin.return_value = mock_ml2
                add_intf.return_value = r_intf
                self.service.get_subnet = mock.Mock()
                self.service.get_subnet.return_value = self._get_subnet_info_dict()
		self.service.core_plugin.create_port = mock.Mock()
                self.service.core_plugin.create_port.return_value = self._get_port_info_dict()
                self.service.get_ports = mock.Mock()
                self.service.get_ports.return_value = [self._get_port_info_dict()]
                self.service.core_plugin.update_port = mock.Mock()
                self.service.add_router_interface(self.context,
                                                  self.router_id,
                                                  r_intf)
                self.service.server.plug_router_interface.assert_called_once_with(
                    network_id=self.network_id,
                    router_id=self.router_id,
                    cidr=self.cidr,
                    subnet_id=self.subnet_id,
                    interface_ip=self.gateway_ip
                )

    def test_remove_router_interface(self):
        r_intf = self._get_router_interface_dict()

        with mock.patch('neutron.db.l3_db.L3_NAT_db_mixin.'
                        'remove_router_interface') as rem_intf:
            self.service.get_ports = mock.Mock()
            self.service.get_ports.return_value = [self._get_port_info_dict()]
            self.service.get_subnet = mock.Mock()
            self.service.get_subnet.return_value = self._get_subnet_info_dict()
            self.service.remove_router_interface(self.context,
                                                 self.router_id,
                                                 r_intf)
            self.service.server.unplug_router_interface.\
                assert_called_once_with(network_id=self.network_id,
                                        router_id=self.router_id,
                                        subnet_id=self.subnet_id,
                                        cidr=self.cidr)

    def test_create_floatingip(self):
        fip = self._get_floatingip_dict(fixed=False)
        with mock.patch('neutron.db.l3_db.L3_NAT_db_mixin.'
                        'create_floatingip') as float_ip:
            float_ip.return_value = self._get_floatingip_dict_server()
            self.service.create_floatingip(self.context, fip)
            self.service.server.create_floatingip.assert_called_once_with(
                floating_network_id=self.floating_net_id,
                fixed_ip_address=self.fixed_ip_address,
                port_id=self.port_id,
                floating_ip_address=self.floating_ip_addr,
                id=self.floating_id,
                status=self.status,
                router_id=self.router_id
            )

    def test_delete_floatingip(self):
        with mock.patch('neutron.db.l3_db.L3_NAT_db_mixin.'
                        'delete_floatingip') as float_ip:
            self.service.delete_floatingip(self.context, self.floating_id)
            self.service.server.delete_floatingip.assert_called_once_with(
                id=self.floating_id
            )

    def test_update_floatingip(self):
        float_data = self._get_floatingip_dict(fixed=True)
        with mock.patch('neutron.db.l3_db.L3_NAT_db_mixin.'
                        'update_floatingip') as float_ip:
            float_ip.return_value = \
                self._get_floatingip_dict_server(fixed=True)
            self.service.get_ports = mock.Mock()
            self.service.get_ports.return_value = [self._get_port_info_dict()]
            self.service.update_floatingip(
                self.context,
                self.floating_id,
                float_data
            )
            self.service.server.update_floatingip.assert_called_once_with(
                floating_network_id=self.floating_net_id,
                fixed_ip_address=self.fixed_ip_address,
                port_id=self.port_id,
                floating_ip_address=self.floating_ip_addr,
                id=self.floating_id,
                subnet_id=self.subnet_id,
                status=self.status,
                router_id=self.router_id
            )

    def _test_disassociate_floatingip(self):
        pass
