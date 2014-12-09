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

from neutron.openstack.common import log as logging
from neutron.i18n import _LI, _LE
from neutron.plugins.common import constants
from neutron.plugins.ml2.drivers.pluribus import config  # noqa
from neutron.db.loadbalancer import loadbalancer_db as ldb
from oslo.config import cfg
from oslo.utils import importutils

LOG = logging.getLogger(__name__)


class PluribusLoadBalancerDriver(object):

    """
    Implementation of the Neutron Loadbalancer Service Plugin's
    Pluribus Driver.

    This class manages the workflow of LBaaS request/response.
    Most DB related works are implemented in class LoadBalancerPlugin
    """

    def __init__(self, plugin):
        """
        Do the initialization for the loadbalancer driver here.
        """
        self.server = importutils.\
            import_object(cfg.CONF.PLURIBUS_PLUGINS['pn_api'])
        self.plugin = plugin
        LOG.info(_LI("PluribusLoadBalancerDriver has been initialised"))

    def create_vip(self, context, vip):
        LOG.debug(("create_vip : ", vip))

        try:
            self.server.create_vip(**vip)
            self.plugin.update_status(context, ldb.Vip, vip['id'],
                                      constants.ACTIVE)
            LOG.info(_LI("Pluribus LB Driver successfully created Vip %s" %
                     vip['id']))
        except Exception as e:
            self.plugin.update_status(context, ldb.Vip, vip['id'],
                                      constants.ERROR)
            LOG.error(_LE("Pluribus LB Driver failed to create Vip %s" %
                      vip['id']))
            raise e

    def delete_vip(self, context, vip):
        LOG.debug(("delete_vip : ", vip))

        try:
            self.server.delete_vip(**vip)

            LOG.info(_LI("Pluribus LB Driver successfully deleted Vip %s" %
                     vip['id']))
        except Exception as e:
            self.plugin.update_status(context, ldb.Vip, vip['id'],
                                      constants.ERROR)
            LOG.error(_LE("Pluribus LB Driver failed to delete Vip %s" %
                      vip['id']))
            raise e

    def create_pool(self, context, pool):
        LOG.debug(("create_pool : ", pool))

        try:
            self.server.create_pool(**pool)
            self.plugin.update_status(context, ldb.Pool, pool['id'],
                                      constants.ACTIVE)
            LOG.info(_LI("Pluribus LB Driver successfully created Pool %s" %
                     pool['id']))
        except Exception as e:
            self.plugin.update_status(context, ldb.Pool, pool['id'],
                                      constants.ERROR)
            LOG.error(_LE("Pluribus LB Driver failed to create Pool %s" %
                      pool['id']))
            raise e

    def delete_pool(self, context, pool):
        LOG.debug(("delete_pool : ", pool))

        try:
            self.server.delete_pool(**pool)
            LOG.info(_LI("Pluribus LB Driver successfully deleted Pool %s" %
                     pool['id']))
        except Exception as e:
            self.plugin.update_status(context, ldb.Pool, pool['id'],
                                      constants.ERROR)
            LOG.error(_LE("Pluribus LB Driver failed to delete Pool %s" %
                      pool['id']))
            raise e

    def create_member(self, context, member):
        LOG.debug(("create_member : ", member))

        try:
            self.server.create_member(**member)
            self.plugin.update_status(context, ldb.Member, member['id'],
                                      constants.ACTIVE)
            LOG.info(_LI("Pluribus LB Driver successfully created Member %s" %
                     member['id']))
            return member
        except Exception as e:
            self.plugin.update_status(context, ldb.Member, member['id'],
                                      constants.ERROR)
            LOG.error(_LE("Pluribus LB Driver failed to create Member %s" %
                      member['id']))
            raise e

    def delete_member(self, context, member):
        LOG.debug(("delete_member : ", member['id']))

        try:
            self.server.delete_member(**member)
            LOG.info(_LI("Pluribus LB Driver successfully deleted Member %s" %
                     member['id']))
        except Exception as e:
            self.plugin.update_status(context, ldb.Member, member['id'],
                                      constants.ERROR)
            LOG.error(_LE("Pluribus LB Driver failed to delete Member %s" %
                      member['id']))
            raise e

    def delete_pool_health_monitor(self, context, health_monitor, pool_id):
        LOG.debug(("delete_health_monitor : ", pool_id))

        try:
            self.server.delete_health(**health_monitor)
            LOG.info(_LI("Pluribus LB Driver successfully created health "
                     "monitor for pool_id %s" % pool_id))
        except Exception as e:
            LOG.error(_LE("Pluribus LB Driver failed to delete health "
                      "monitor for pool_id %s" % pool_id))
            self.plugin.update_pool_health_monitor(context,
                                                   health_monitor["id"],
                                                   pool_id,
                                                   constants.ERROR)
            raise e

    def create_pool_health_monitor(self, context, health_monitor, pool_id):
        LOG.debug(("create_health_monitor : ", health_monitor, pool_id))

        try:
            LOG.debug(("create_health", health_monitor))
            self.server.create_health(**health_monitor)
            self.plugin.update_pool_health_monitor(context,
                                                   health_monitor["id"],
                                                   pool_id,
                                                   constants.ACTIVE)
            LOG.info(_LI("Pluribus LB Driver successfully created health "
                     "monitor for pool_id %s" % pool_id))
            return health_monitor
        except Exception as e:
            LOG.error(_LE("Pluribus LB Driver failed to create health "
                      "monitor for pool_id %s" % pool_id))
            self.plugin.update_pool_health_monitor(context,
                                                   health_monitor["id"],
                                                   pool_id,
                                                   constants.ERROR)
