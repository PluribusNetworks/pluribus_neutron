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

from neutron.services.l3_router.l3_pluribus import PluribusRouterPlugin
from neutron.plugins.ml2.drivers.pluribus import mech_pluribus as pluribus
from neutron.plugins.common import constants
from neutron.tests import base
from oslo.config import cfg
from neutron import manager


class Network(object):

    network_id = "net-1"
    network_name = "n1"
    segmentation_id = 3999


class Subnet(object):

    subnet_id = "sub-1"
    subnet_name = "s1"
    ip_version = 4
    cidr = "180.0.0.0/24",
    gateway_ip = "180.0.0.1"
    ip_address = "180.0.0.2"


class Port(object):

    port_id = "port-1"
    port_name = "p1"


class FakeNetworkContext(object):

    """To generate network context for testing purposes only."""

    def __init__(self, network, segments=None):
        self._network = network
        self._segments = segments

    @property
    def current(self):
        return self._network

    @property
    def network_segments(self):
        return self._segments


class FakePortContext(object):

    """To generate port context for testing purposes only."""

    def __init__(self, port, network):
        self._port = port
        self._network_context = network

    @property
    def current(self):
        return self._port

    @property
    def network(self):
        return self._network_context


class FakeSubnetContext(object):

    """To generate subnet context for testing purposes only."""

    def __init__(self, subnet):
        self._subnet = subnet

    @property
    def current(self):
        return self._subnet


class PluribusDriverTestCase(base.BaseTestCase,
                             Network,
                             Subnet,
                             Port):

    """Test case for Pluribus ML2 driver."""

    @mock.patch('oslo.utils.importutils.import_object')
    @mock.patch('neutron.plugins.ml2.plugin.Ml2Plugin')
    @mock.patch('neutron.services.l3_router.l3_pluribus.PluribusRouterPlugin')
    def setUp(self, mock_server, mock_ml2, mock_l3):
        super(PluribusDriverTestCase, self).setUp()
        self.driver = pluribus.PluribusDriver()
        self.driver.server = mock_server
        self.tenant_id = "tenant-1"

        self.fake_ml2 = mock_ml2
        self.fake_l3 = mock_l3

    def _set_network_config(self, external=False):
        self.network_context = self._get_network_context(external)
        self.net_info = self.network_context.current

    def _set_subnet_config(self, external=False):
        self.network_context = self._get_network_context(external)

        self.subnet_context = self._get_subnet_context()
        self.subnet_context._plugin_context = self.subnet_context

        self.subnet_info = self.subnet_context.current
        self.subnet_info['dhcp_ip'] = self.ip_address
        self.subnet_info['pn_dhcp'] = True
        self.net_info = self.network_context.current

    def _set_port_config(self):
        self.network_context = self._get_network_context()
        self.port_context = self._get_port_context()

        self.port_context._plugin_context = self.port_context
        self.net_info = self.network_context.current
        self.port_info = self.port_context.current

    def mock_create_port(self):
        self._set_port_config()

        self.fake_ml2.create_port = mock.Mock()
        self.fake_ml2.create_port.return_value = self.port_info

        self.fake_ml2.get_ports = mock.Mock()
        self.fake_ml2.get_ports.return_value = [self.port_info]

        self.fake_ml2.update_port = mock.Mock()

    def test_create_network_on_valid_config(self):
        self._set_network_config()
        self.driver.create_network_postcommit(self.network_context)
        self.driver.server.create_network.assert_called_once_with(
            status=self.net_info["status"],
            subnets=self.net_info["subnets"],
            name=self.net_info["name"],
            admin_state_up=self.net_info["admin_state_up"],
            shared=self.net_info["shared"],
            id=self.net_info["id"],
            router_external=self.net_info["router_external"],
            tenant_id=self.net_info["tenant_id"]
        )

    def test_delete_network_on_valid_config(self):
        self._set_network_config(external=False)

        self.driver.delete_network_postcommit(self.network_context)
        self.driver.server.delete_network.assert_called_once_with(
            status=self.net_info["status"],
            subnets=self.net_info["subnets"],
            name=self.net_info["name"],
            admin_state_up=self.net_info["admin_state_up"],
            shared=self.net_info["shared"],
            id=self.net_info["id"],
            router_external=self.net_info["router_external"],
            tenant_id=self.net_info["tenant_id"]
        )

    def test_create_subnet_on_internal_network_valid(self):
        self._set_subnet_config(external=False)
        self.mock_create_port()

        manager.NeutronManager.get_plugin = mock.Mock()
        manager.NeutronManager.get_plugin.return_value = self.fake_ml2
        self.fake_ml2.get_network = mock.Mock()
        self.fake_ml2.get_network.return_value = self.net_info

        self.driver.create_subnet_postcommit(self.subnet_context)

        self.driver.server.create_subnet.assert_called_once_with(
            dhcp_ip=self.subnet_info['dhcp_ip'],
            name=self.subnet_info['name'],
            id=self.subnet_info['id'],
            ip_version=self.subnet_info['ip_version'],
            shared=self.subnet_info['shared'],
            cidr=self.subnet_info['cidr'],
            gateway_ip=self.subnet_info['gateway_ip'],
            network_id=self.subnet_info['network_id'],
            tenant_id=self.subnet_info['tenant_id'],
            pn_dhcp=self.subnet_info['pn_dhcp'],
            enable_dhcp=self.subnet_info['enable_dhcp']
        )

    def test_delete_subnet_on_valid_config(self):
        self._set_subnet_config()

        self.driver.delete_subnet_postcommit(self.subnet_context)
        self.driver.server.delete_subnet.assert_called_once_with(
            name=self.subnet_info['name'],
            id=self.subnet_info['id'],
            ip_version=self.subnet_info['ip_version'],
            shared=self.subnet_info['shared'],
            cidr=self.subnet_info['cidr'],
            gateway_ip=self.subnet_info['gateway_ip'],
            network_id=self.subnet_info['network_id'],
            tenant_id=self.subnet_info['tenant_id'],
            dhcp_ip=self.subnet_info['dhcp_ip'],
            pn_dhcp=self.subnet_info['pn_dhcp'],
            enable_dhcp=self.subnet_info['enable_dhcp']
        )

    def test_create_port_on_valid_config(self):
        self._set_port_config()
        self.driver.create_port_postcommit(self.port_context)
        self.driver.server.create_port.assert_called_once_with(
            device_owner=self.port_info['device_owner'],
            fixed_ips=self.port_info['fixed_ips'],
            id=self.port_info['id'],
            name=self.port_info['name'],
            admin_state_up=self.port_info['admin_state_up'],
            tenant_id=self.port_info['tenant_id'],
            network_id=self.port_info['network_id']
        )

    def test_delete_port_on_valid_config(self):
        self._set_port_config()
        manager.NeutronManager.get_service_plugins = mock.Mock()
        manager.NeutronManager.get_service_plugins.return_value = {
            constants.L3_ROUTER_NAT: self.fake_l3}
        self.fake_l3.disassociate_floatingips = mock.Mock()
        self.driver.delete_port_postcommit(self.port_context)
        self.driver.server.delete_port.assert_called_once_with(
            device_owner=self.port_info['device_owner'],
            fixed_ips=self.port_info['fixed_ips'],
            id=self.port_info['id'],
            name=self.port_info['name'],
            admin_state_up=self.port_info['admin_state_up'],
            tenant_id=self.port_info['tenant_id'],
            network_id=self.port_info['network_id']
        )

    def _get_network_dict(self, external):
        network = {
            "status": "ACTIVE",
            "subnets": [],
            "name": self.network_name,
            "admin_state_up": True,
            "shared": False,
            "id": self.network_id,
            "router:external": external,
            "tenant_id": self.tenant_id
        }

        return network

    def _get_network_context(self, external=False):
        network = self._get_network_dict(external)
        network_segments = [{"segmentation_id": self.segmentation_id}]

        return FakeNetworkContext(network, network_segments)

    def _get_port_context(self, device_owner=""):
        port = {
            "device_owner": device_owner,
            "fixed_ips": [
                {
                    'subnet_id': self.subnet_id,
                    'ip_address': self.ip_address
                }
            ],
            "id": self.port_id,
            "name": self.port_name,
            "admin_state_up": True,
            "tenant_id": self.tenant_id,
            "network_id": self.network_id
        }

        network = self._get_network_dict(external=False)
        return FakePortContext(port, network)

    def _get_subnet_context(self):
        subnet = {
            "name": self.subnet_name,
            "id": self.subnet_id,
            "ip_version": self.ip_version,
            "shared": False,
            "cidr": self.cidr,
            "gateway_ip": self.gateway_ip,
            "network_id": self.network_id,
            "tenant_id": self.tenant_id,
            "enable_dhcp": True,
        }
        return FakeSubnetContext(subnet)

    def _get_dhcp_port_context(self):
        return _get_port_context(tenant_id, net_id, network,
                                 device_owner="network:dhcp")
