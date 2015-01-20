# COPYRIGHT 2015 Pluribus Networks Inc.
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
