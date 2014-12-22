# COPYRIGHT 2014 Pluribus Networks Inc.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

import mock
from neutron.services.loadbalancer.drivers.pluribus.lb_pluribus \
    import PluribusLoadBalancerDriver
from neutron.tests import base


class Pool(object):
    lb_method = 'ROUND_ROBIN'
    protocol = 'TCP'
    name = 'testpool'
    subnet_id = 'sub-1'
    pool_id = 'pool-1'
    vip_id = None
    provider = 'pluribus'


class Member(object):
    weight = 1
    address = '150.0.0.3'
    protocol_port = 22
    member_id = 'member-1'


class HealthMonitor(object):
    delay = 10
    max_retries = 3
    timeout = 3
    pools = {'status': 'PENDING_CREATE',
             'status_description': None}
    type = 'TCP'
    healthmonitor_id = 'hm-1'


class Vip(object):
    protocol = 'TCP'
    address = '150.0.0.4'
    protocol_port = 22
    vip_id = 'vip-1'
    vip_name = 'vip'
    subnet_id = 'sub-1'
    connection_limit = -1
    pool_id = 'pool-1'


class FakeContext(object):

    """Fake context for testing purposes only"""
    def __init__(self):
        pass


class PluribusLoadBalancerTestCase(base.BaseTestCase,
                                   Vip,
                                   Pool,
                                   Member,
                                   HealthMonitor):

    """Test cases for Pluribus LoadBalancer"""

    @mock.patch('oslo.utils.importutils.import_object')
    @mock.patch('neutron.services.loadbalancer.drivers.common.'
                'agent_driver_base.LoadBalancerCallbacks')
    def setUp(self, mock_server, mock_plugin):
        super(PluribusLoadBalancerTestCase, self).setUp()
        self.service = PluribusLoadBalancerDriver(mock_plugin)
        self.service.server = mock_server
        self.pools['pool_id'] = self.pool_id
        self.tenant_id = "tenant-1"
        self.context = FakeContext()

    def _create_pool_dict(self):
        pool = {
            'lb_method': self.lb_method,
            'protocol': self.protocol,
            'name': self.name,
            'subnet_id': self.subnet_id,
            'id': self.pool_id,
            'provider': self.provider
        }

        return pool

    def _create_member_dict(self):
        member = {
            'weight': self.weight,
            'address': self.address,
            'protocol_port': self.protocol_port,
            'id': self.member_id
        }

        return member

    def _create_vip_dict(self):
        vip = {
            'protocol': self.protocol,
            'address': self.address,
            'protocol_port': self.protocol_port,
            'id': self.vip_id,
            'vip_name': self.vip_name,
            'subnet_id': self.subnet_id,
            'connection_limit': self.connection_limit,
            'pool_id': self.pool_id
        }

        return vip

    def _create_health_monitor(self):
        hm = {
            'delay': self.delay,
            'max_retries': self.max_retries,
            'timeout': self.timeout,
            'pools': self.pools,
            'type': self.type,
            'id': self.healthmonitor_id
        }

        return hm

    def test_create_pool(self):

        pool = self._create_pool_dict()
        self.service.create_pool(self.context, pool)
        self.service.server.create_pool.assert_called_once_with(
            lb_method=self.lb_method,
            protocol=self.protocol,
            name=self.name,
            subnet_id=self.subnet_id,
            id=self.pool_id,
            provider=self.provider
        )

    def test_delete_pool(self):

        pool = self._create_pool_dict()
        self.service.delete_pool(self.context, pool)
        self.service.server.delete_pool.assert_called_once_with(
            lb_method=self.lb_method,
            protocol=self.protocol,
            name=self.name,
            subnet_id=self.subnet_id,
            id=self.pool_id,
            provider=self.provider
        )

    def test_create_member(self):

        member = self._create_member_dict()
        self.service.create_member(self.context, member)
        self.service.server.create_member.assert_called_once_with(
            weight=self.weight,
            address=self.address,
            protocol_port=self.protocol_port,
            id=self.member_id
        )

    def test_delete_member(self):

        member = self._create_member_dict()
        self.service.delete_member(self.context, member)
        self.service.server.delete_member.assert_called_once_with(
            weight=self.weight,
            address=self.address,
            protocol_port=self.protocol_port,
            id=self.member_id
        )

    def test_create_vip(self):
        vip = self._create_vip_dict()
        self.service.create_vip(self.context, vip)
        self.service.server.create_vip.assert_called_once_with(
            protocol=self.protocol,
            address=self.address,
            protocol_port=self.protocol_port,
            id=self.vip_id,
            vip_name=self.vip_name,
            subnet_id=self.subnet_id,
            connection_limit=self.connection_limit,
            pool_id=self.pool_id
        )

    def test_delete_vip(self):
        vip = self._create_vip_dict()
        self.service.delete_vip(self.context, vip)
        self.service.server.delete_vip.assert_called_once_with(
            protocol=self.protocol,
            address=self.address,
            protocol_port=self.protocol_port,
            id=self.vip_id,
            vip_name=self.vip_name,
            subnet_id=self.subnet_id,
            connection_limit=self.connection_limit,
            pool_id=self.pool_id
        )

    def test_create_pool_health_monitor(self):
        hm = self._create_health_monitor()
        self.service.create_pool_health_monitor(self.context, hm,
                                                self.pool_id)
        self.service.server.create_health.assert_called_once_with(
            delay=self.delay,
            max_retries=self.max_retries,
            timeout=self.timeout,
            pools=self.pools,
            type=self.type,
            id=self.healthmonitor_id,
        )

    def test_delete_pool_health_monitor(self):
        hm = self._create_health_monitor()
        self.service.delete_pool_health_monitor(self.context, hm,
                                                self.pool_id)
        self.service.server.delete_health.assert_called_once_with(
            delay=self.delay,
            max_retries=self.max_retries,
            timeout=self.timeout,
            pools=self.pools,
            type=self.type,
            id=self.healthmonitor_id,
        )
