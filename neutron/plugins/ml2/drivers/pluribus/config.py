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

pluribus_plugin_opts = [
    cfg.StrOpt(
        'pn_switch',
        default='',
        help='Pluribus Switch to connect to'),
    cfg.IntOpt(
        'pn_port',
        default=25000,
        help='Pluribus Port to connect to'),
    cfg.StrOpt(
        'pn_api',
        help='The wrapper class to send RPC requests')]

cfg.CONF.register_opts(pluribus_plugin_opts, "PLURIBUS_PLUGINS")
