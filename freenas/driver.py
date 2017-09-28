# Manilla driver for FreeNAS
# Copyright (c) 2017 Agatti Software Labs. All Rights Reserved.
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

from manila import exception
from manila.i18n import _
from manila.share import driver
from manila.share.drivers.freenas import options
from manila.share.drivers.freenas import process_req
from oslo_log import log


VERSION = '1.0'
LOG = log.getLogger(__name__)


# FreeNAS Manilla driver main interface from OpenStack
class FreeNasDriver(driver.ShareDriver):
    """Freenas Manilla Driver for NFS shares.

    API version history:
        1.0 - Initial version.
    """

    def __init__(self, *args, **kwargs):
        """Do initialization."""
        LOG.debug('Initializing FreeNAS Manilla NFS driver.')
        # TODO(RS-AGT): Add configuration options according to nfs/cifs share
        # in options.py, Currently now only NFS share is supported.
        super(FreeNasDriver, self).__init__(False, *args, **kwargs)
        self.configuration = kwargs.get('configuration')
        if self.configuration:
            self.configuration.append_config_values(
                options.freenas_connection_opts)
            self.configuration.append_config_values(
                options.freenas_nfs_opts)
            self.configuration.append_config_values(
                options.freenas_dataset_opts)
            self.configuration.append_config_values(
                options.freenas_transport_opts)
            self.helper = process_req.FreeNASProcessRequests(self.configuration)
        else:
            raise exception.BadConfigurationException(
                reason=_('FreeNAS configuration missing.'))

    @property
    def share_backend_name(self):
        if not hasattr(self, '_share_backend_name'):
            self._share_backend_name = None
            if self.configuration:
                self._share_backend_name = self.configuration.safe_get(
                    'share_backend_name')
            if not self._share_backend_name:
                self._share_backend_name = 'AgattiL'
        return self._share_backend_name

    def do_setup(self, context):
        """Any initialization the FreeNAS driver does while starting."""
        LOG.debug('Setting up the FreeNAS plugin.')
        return self.helper.do_setup()

    def check_for_setup_error(self):
        """check for after setup error"""
        self.helper.check_for_setup_error()

    def create_share(self, context, share, share_server=None):
        """Create a NFS share."""
        LOG.debug('Share Name:  %s', share['name'])
        return self.helper.create_dataset(share)

    def create_share_from_snapshot(self, context, share, snapshot,
                                   share_server=None):
        LOG.debug('Old Share Name:  %s  Clone Share name %s',
                  snapshot['share_name'], share['name'])
        return self.helper.create_share_from_snapshot(share, snapshot)

    def delete_share(self, context, share, share_server=None):
        """Delete a share."""
        LOG.debug('Deleting share %s.', share['name'])
        self.helper.delete_share(share['name'])

    def extend_share(self, share, new_size, share_server=None):
        """Extends a share."""
        LOG.debug('Extending share %(name)s to %(size)sG.', {
            'name': share['name'], 'size': new_size})
        self.helper.set_quota(share['name'], new_size)

    def create_snapshot(self, context, snapshot, share_server=None):
        """Create Snapshot"""
        LOG.debug('Creating a snapshot of share %s', snapshot['share_name'])
        return self.helper.create_snapshot(snapshot['share']['name'],
                                           snapshot['name'])

    def delete_snapshot(self, context, snapshot, share_server=None):
        LOG.debug('Deleting a snapshot of share %s.', snapshot['share_name'])
        self.helper.delete_snapshot(snapshot['share']['name'],
                                    snapshot['name'])

    def update_access(self, context, share, access_rules, add_rules,
                      delete_rules, share_server=None):
        # TODO(RS-AGT): Need to add user specific access for share
        # Currently passing default access permission for Share.
        pass

    def _update_share_stats(self, data=None):
        super(FreeNasDriver, self)._update_share_stats()
        data = self.helper.update_share_stats()
        data['driver_version'] = VERSION
        data['share_backend_name'] = self.share_backend_name
        self._stats.update(data)
