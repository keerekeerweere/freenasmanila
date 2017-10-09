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


# Helper utility for manila nfs driver
from oslo_log import log

from manila import exception
from manila.i18n import _
from manila.share.drivers.freenas.freenasapi import FreeNASApiError
from manila.share.drivers.freenas.freenasapi import FreeNASServer
from manila.share.drivers.freenas import utils
import simplejson as json

LOG = log.getLogger(__name__)

# All the OpenStack share manila share related requests for FreeNAS are
# Processed here and corresponding FreeNAS REST API formed and invoked.


class FreeNASProcessRequests(object):

    def __init__(self, configuration):
        self.config = configuration
        self.nfs_mount_point_base = (
            self.config.freenas_mount_point_base)
        self.dataset_compression = (
            self.config.freenas_dataset_compression)
        self.dataset_dedupe = self.config.freenas_dataset_dedupe
        self.storage_protocol = 'NFS'
        self.handle = None

    def _create_handle(self, **kwargs):
        """Instantiate handle (client) for API communication with

           FreeNAS server
        """
        host_system = kwargs['hostname']
        LOG.debug('FreeNAS server: %s', host_system)
        self.handle = FreeNASServer(host=host_system,
                                    port=kwargs['port'],
                                    username=kwargs['login'],
                                    password=kwargs['password'],
                                    api_version=kwargs['api_version'],
                                    transport_type=kwargs['transport_type'],
                                    style=FreeNASServer.STYLE_LOGIN_PASSWORD)
        if not self.handle:
            raise FreeNASApiError("Failed to create handle for \
                                   FREENAS server")

    def do_setup(self):
        """Create REST API handle to FreeNAS Server."""

        self._create_handle(hostname=self.config.freenas_server_hostname,
                            port=self.config.freenas_server_port,
                            login=self.config.freenas_login,
                            password=self.config.freenas_password,
                            api_version=self.config.freenas_api_version,
                            transport_type=self.config.freenas_transport_type)
        if not self.handle:
                raise FreeNASApiError("Failed to create handle \
                                       for FREENAS server")

    def check_for_setup_error(self):
        """Check prerequisite to met for driver functionality"""

        if self.config.freenas_dataset != FreeNASServer.DS_NAME:
            raise FreeNASApiError("Volume name must be agattivol \
                                  for creating share")

        vol_req = ('%s/%s') % (FreeNASServer.REST_API_VOLUME,
                               self.config.freenas_dataset)

        vol_resp = self.handle.invoke_command(FreeNASServer.SELECT_COMMAND,
                                              vol_req, None)

        if (json.loads(vol_resp['response'])['name'] !=
                FreeNASServer.DS_NAME):
            raise FreeNASApiError("Top Level volume name \
                                   must be agattivol")

    def _create_nfs_share(self, mountpoint):
        nfsparams = {}
        nfsparams['nfs_paths'] = mountpoint.split()

        nfs_req = ('%s/') % (FreeNASServer.REST_API_SHARE)

        LOG.debug('create share parmas : %s', json.dumps(nfsparams))
        nfs_resp = self.handle.invoke_command(FreeNASServer.CREATE_COMMAND,
                                              nfs_req, json.dumps(nfsparams))

        LOG.debug('create NFS share response : %s', json.dumps(nfs_resp))
        if nfs_resp['status'] != FreeNASServer.STATUS_OK:
            msg = ('Error while creating dataset: %s' % nfs_resp['response'])
            raise FreeNASApiError('Unexpected error', msg)

    def create_dataset(self, share):
        """Create dataset on FreeNAS

           Export dataset as NFS share.
           Return export nfs share path.
        """
        LOG.debug('create share: %s', share['name'])
        dataset = utils.generate_share_name(share['name'],
                                            self._get_mount_path())
        dataset['refquote'] = str(share['size']) + "G"
        dataset['dedup'] = self.dataset_dedupe
        dataset['compression'] = self.dataset_dedupe

        LOG.debug('create dataset parmas : %s', json.dumps(dataset))
        ds_req = ('%s/%s/%s/') % (FreeNASServer.REST_API_VOLUME,
                                  self.config.freenas_dataset,
                                  FreeNASServer.DATASET)

        ds_resp = self.handle.invoke_command(FreeNASServer.CREATE_COMMAND,
                                             ds_req, json.dumps(dataset))

        LOG.debug('create dataset response : %s', json.dumps(ds_resp))
        if ds_resp['status'] != FreeNASServer.STATUS_OK:
            msg = ('Error while creating dataset: %s' % ds_resp)
            raise FreeNASApiError('Unexpected error', msg)

        LOG.info('Created share %s for shareID %s',
                 dataset['name'], share['share_id'])
        self._create_nfs_share(dataset['mountpoint'])
        path = self._get_share_path(dataset['name'])
        return [self._get_location_path(path, share['share_proto'])]

    def set_quota(self, share, new_size):
        """Update quota size for freenas share. """

        qt_params = utils.generate_share_name(share['name'],
                                              self._get_mount_path())
        qt_params['refquote'] = '%sG' % new_size

        qt_req = ('%s/%s/%s/%s') % (FreeNASServer.REST_API_VOLUME,
                                    self.config.freenas_dataset,
                                    FreeNASServer.DATASET, qt_params['name'])

        qt_resp = self.handle.invoke_command(FreeNASServer.CREATE_COMMAND,
                                             qt_req, json.dumps(qt_params))

        LOG.debug('Update dataset response : %s', json.dumps(qt_resp))
        if qt_resp['status'] != FreeNASServer.STATUS_OK:
            msg = ('Error while creating dataset: %s' % qt_resp['response'])
            raise FreeNASApiError('Unexpected error', msg)

    def _get_mount_path(self):
        return (self.nfs_mount_point_base + "/"
                + self.config.freenas_dataset)

    def _get_location_path(self, path, protocol):
        location = None
        if protocol == self.config.freenas_storage_protocol:
            location = {'path': '%s:%s' %
                        (self.config.freenas_server_hostname,
                         path)}
        else:
            raise exception.InvalidShare(
                reason=(_('Only NFS protocol is currently supported.')))
        return location

    def delete_share(self, share):
        """Delete share."""
        share_name = utils.generate_share_name(share['name'],
                                               self._get_mount_path())

        del_req = ("%s/%s/%s/%s/") % (FreeNASServer.REST_API_VOLUME,
                                      self.config.freenas_dataset,
                                      FreeNASServer.DATASET,
                                      share_name['name'])

        LOG.debug('Delete dataset request : %s', del_req)
        del_resp = self.handle.invoke_command(FreeNASServer.DELETE_COMMAND,
                                              del_req, None)

        LOG.debug('Delete dataset response : %s', json.dumps(del_resp))
        if del_resp['status'] != FreeNASServer.STATUS_OK:
            msg = ('Error while creating dataset: %s' % del_resp['response'])
            raise FreeNASApiError('Unexpected error', msg)

    def _get_share_path(self, share_name):
        return '%s/%s/%s' % (self.nfs_mount_point_base,
                             self.config.freenas_dataset,
                             share_name)

    def _get_volume_stat(self):

        request_urn = ('%s/%s/') % (FreeNASServer.REST_API_VOLUME,
                                    self.config.freenas_dataset)

        LOG.debug('request_urn : %s', request_urn)
        ret = self.handle.invoke_command(FreeNASServer.SELECT_COMMAND,
                                         request_urn, None)

        return ((utils.get_size_in_gb(json.loads(ret['response'])['avail']
                + json.loads(ret['response'])['used'])),
                utils.get_size_in_gb(json.loads(ret['response'])['avail']),
                utils.get_size_in_gb(json.loads(ret['response'])['used']))

    def update_share_stats(self):
        """Update driver capabilities."""

        total, free, allocated = self._get_volume_stat()
        compression = not self.dataset_compression == 'off'
        dedupe = not self.dataset_dedupe == 'off'
        return {
            'vendor_name': 'FreeNAS',
            'storage_protocol': self.storage_protocol,
            'nfs_mount_point_base': self.nfs_mount_point_base,
            'pools': [{
                'pool_name': self.config.freenas_dataset,
                'total_capacity_gb': total,
                'free_capacity_gb': free,
                'snapshot_support': True,
                'create_share_from_snapshot_support': True,
                'reserved_percentage':
                    self.config.reserved_share_percentage,
                'compression': compression,
                'dedupe': dedupe,
                'thin_provisioning': self.config.freenas_thin_provisioning,
            }],
        }

    def create_snapshot(self, snapshot):
        """Create snapshot of given share. """

        share_params = utils.generate_share_name(snapshot['share']['name'],
                                                 self._get_mount_path())
        snap_params = {}
        snap_params['dataset'] = ('%s/%s') % (self.config.freenas_dataset,
                                              share_params['name'])
        snap_params['name'] = utils.generate_snapshot_name(snapshot['name'])
        request_urn = ('%s/') % (FreeNASServer.REST_API_SNAPSHOT)

        LOG.debug('Snaps params %s', json.dumps(snap_params))
        ret = self.handle.invoke_command(FreeNASServer.CREATE_COMMAND,
                                         request_urn, json.dumps(snap_params))
        if ret['status'] != FreeNASServer.STATUS_OK:
            msg = ('Error while creating snapshot: %s' % ret['response'])
            raise FreeNASApiError('Unexpected error', msg)

        model_update = {'provider_location': '%s@%s' %
                        (self._get_share_path(share_params['name']),
                         snap_params['name'])}
        return model_update

    def delete_snapshot(self, snapshot):
        """delete snapshot of given share. """

        snap_params = utils.generate_share_name(snapshot['share']['name'],
                                                self._get_mount_path())
        snap_name = utils.generate_snapshot_name(snapshot['name'])

        request_urn = ('%s/%s/%s@%s/') % (FreeNASServer.REST_API_SNAPSHOT,
                                          self.config.freenas_dataset,
                                          snap_params['name'], snap_name)
        LOG.debug('Snaps del req %s', request_urn)

        ret = self.handle.invoke_command(FreeNASServer.DELETE_COMMAND,
                                         request_urn, None)
        if ret['status'] != FreeNASServer.STATUS_OK:
            msg = ('Error while creating snapshot: %s' % ret['response'])
            raise FreeNASApiError('Unexpected error', msg)

    def create_share_from_snapshot(self, share, snapshot):
        """Create Cloned dataset on freenas

           Export dataset as NFS share.
           Return exported path of NFS share.
        """
        base_ds = utils.generate_share_name(snapshot['share_name'],
                                            self._get_mount_path())
        snap_name = utils.generate_snapshot_name(snapshot['name'])
        clone_ds = utils.generate_share_name(share['name'],
                                             self._get_mount_path())
        clone_ds['refquota'] = str(share['size']) + 'G'
        clone_args = {}
        clone_args['name'] = ("%s/%s") % (self.config.freenas_dataset,
                                          clone_ds['name'])

        clone_req = ('%s/%s/%s@%s/%s/') % (FreeNASServer.REST_API_SNAPSHOT,
                                           self.config.freenas_dataset,
                                           base_ds['name'], snap_name,
                                           FreeNASServer.CLONE)

        clone_resp = self.handle.invoke_command(FreeNASServer.CREATE_COMMAND,
                                                clone_req,
                                                json.dumps(clone_args))
        if clone_resp['status'] != FreeNASServer.STATUS_OK:
            msg = ('Error while creating snapshot: %s' %
                   clone_resp['response'])
            raise FreeNASApiError('Unexpected error', msg)

        self._create_nfs_share(clone_ds['mountpoint'])
        path = self._get_share_path(clone_ds['name'])
        return [self._get_location_path(path, share['share_proto'])]
