# Manila driver for FreeNAS
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

import ddt
import json
from oslo_config import cfg

from manila import context
from manila import exception
from manila.share import configuration
from manila.share.drivers.freenas import driver
from manila.share.drivers.freenas.freenasapi import FreeNASApiError
from manila.share.drivers.freenas.freenasapi import FreeNASServer
from manila.share.drivers.freenas.process_req import FreeNASProcessRequests
from manila import test
from mock import patch
from mock import PropertyMock

test_config = configuration.Configuration(None)
test_config.freenas_server_hostname = '1.1.1.1'
test_config.freenas_api_version = 'v1.0'
test_config.freenas_server_port = 3000
test_config.freenas_volume_backend_name = 'TEST'
test_config.freenas_vendor_name = 'FreeNAS'
test_config.freenas_storage_protocol = 'NFS'
test_config.freenas_login = 'freenas_user'
test_config.freenas_password = 'freenas_password'
test_config.freenas_mount_point_base = '/mnt'
test_config.freenas_dataset = 'testvol'
test_config.freenas_dataset_compression = 'on'
test_config.freenas_dataset_dedupe = 'on'
test_config.freenas_thin_provisioning = False
test_config.share_backend_name = 'AgattiL'
FAKE_SHARE_NAME = 'agtshare-1234'
FAKE_SNAPSHOT_NAME = 'agtsnap-1234'

CONF = cfg.CONF


class FakeResponse(object):

    def __init__(self, response={}):
        self.content = json.dumps(response)
        super(FakeResponse, self).__init__()

    def close(self):
        pass


@ddt.ddt
class TestFreeNasDriver(test.TestCase):

    def __init__(self, *args, **kwds):
        super(TestFreeNasDriver, self).__init__(*args, **kwds)
        self._ctx = context.get_admin_context()
        self.configuration = test_config

    def setUp(self):
        CONF.set_default('driver_handles_share_servers', False)
        self._driver = driver.FreeNasDriver(
            configuration=self.configuration)
        self._driver.do_setup(self._ctx)
        super(TestFreeNasDriver, self).setUp()

    def _get_share_path(self):
        return '%s/%s/%s' % (test_config.freenas_mount_point_base,
                             test_config.freenas_dataset,
                             FAKE_SHARE_NAME)

    @patch.object(FreeNASServer, 'invoke_command')
    def test_check_setup_error__invalid_config_vol(self, mock_rest_cmd):
        mock_rest_cmd.return_value = {}
        self.assertRaises(
            FreeNASApiError, self._driver.check_for_setup_error)

    @patch.object(FreeNASServer, 'invoke_command')
    def test_check_setup_error__volume_does_not_exist(self, mock_rest_cmd):
        test_config.freenas_dataset = 'agattivol'
        mock_rest_cmd.return_value = {'response': json.dumps({'name': 'adsfsdf'})}
        self.assertRaises(
            FreeNASApiError, self._driver.check_for_setup_error)

    @patch.object(FreeNASServer, 'invoke_command')
    def test_create_share(self, mock_rest_cmd):

        share = {
            'name': 'share-1234-4567-78787',
            'size': 1,
            'share_id': 'share-1234-4567-78787',
            'share_proto': test_config.freenas_storage_protocol
        }
        location = {
            "path": '%s:%s/%s/%s' % (test_config.freenas_server_hostname,
                                     test_config.freenas_mount_point_base,
                                     test_config.freenas_dataset,
                                     FAKE_SHARE_NAME)
        }
        mock_rest_cmd.return_value = {'status': 'ok'}
        self.assertEqual([location],
                         self._driver.create_share(self._ctx, share))

    @patch.object(FreeNASServer, 'invoke_command')
    def test_create_share_wrong_proto(self, mock_rest_cmd):

        share = {
            'name': 'share-1234-4567-78787',
            'size': 1,
            'share_id': 'share-1234-4567-78787',
            'share_proto': 'INVALID_PROTOCOL'
        }

        mock_rest_cmd.return_value = {'status': 'ok'}
        self.assertRaises(exception.InvalidShare,
                          self._driver.create_share,
                          self._ctx, share)

    @patch.object(FreeNASServer, 'invoke_command')
    def test_delete_share(self, mock_rest_cmd):

        share = {
            'name': 'share-1234-4567-78787',
            'size': 1,
            'share_id': 'share-1234-4567-78787',
            'share_proto': test_config.freenas_storage_protocol
        }
        mock_rest_cmd.return_value = {'status': 'ok'}

        del_req = ("%s/%s/%s/%s/") % (FreeNASServer.REST_API_VOLUME,
                                      test_config.freenas_dataset,
                                      FreeNASServer.DATASET,
                                      FAKE_SHARE_NAME)
        self._driver.delete_share(self._ctx, share)
        mock_rest_cmd.assert_any_call(FreeNASServer.DELETE_COMMAND,
                                      del_req, None)

    @patch.object(FreeNASServer, 'invoke_command')
    def test_delete_share_with_error(self, mock_rest_cmd):

        share = {
            'name': 'share-1234-4567-78787',
            'size': 1,
            'share_id': 'share-1234-4567-78787',
            'share_proto': test_config.freenas_storage_protocol
        }
        mock_rest_cmd.return_value = {'status': 'error',
                                      'response': 'error delting share'}

        self.assertRaises(FreeNASApiError,
                          self._driver.delete_share,
                          self._ctx, share)

    @patch.object(FreeNASServer, 'invoke_command')
    def test_extend_share(self, mock_rest_cmd):

        share = {
            'name': 'share-1234-4567-78787',
            'size': 1,
            'share_id': 'share-1234-4567-78787',
            'share_proto': test_config.freenas_storage_protocol
        }
        new_size = 4
        extend_params = {}
        extend_params['name'] = FAKE_SHARE_NAME
        extend_params['mountpoint'] = (test_config.freenas_mount_point_base
                                       + "/" + test_config.freenas_dataset
                                       + "/" + FAKE_SHARE_NAME)
        extend_params['refquote'] = '%sG' % new_size

        extend_req = ('%s/%s/%s/%s') % (FreeNASServer.REST_API_VOLUME,
                                        test_config.freenas_dataset,
                                        FreeNASServer.DATASET,
                                        FAKE_SHARE_NAME)

        mock_rest_cmd.return_value = {'status': 'ok'}
        self._driver.extend_share(share, new_size)

        mock_rest_cmd.assert_called_with(FreeNASServer.CREATE_COMMAND,
                                         extend_req, json.dumps(extend_params))

    @patch.object(FreeNASServer, 'invoke_command')
    def test_extend_share__with_error(self, mock_rest_cmd):

        share = {
            'name': 'share-1234-4567-78787',
            'size': 1,
            'share_id': 'share-1234-4567-78787',
            'share_proto': test_config.freenas_storage_protocol
        }
        new_size = 4

        mock_rest_cmd.return_value = {'status': 'error',
                                      'response': 'error extending share'}

        self.assertRaises(FreeNASApiError,
                          self._driver.extend_share,
                          share, new_size)

    @patch.object(FreeNASServer, 'invoke_command')
    def test_create_snapshot(self, mock_rest_cmd):

        share = {
            'name': 'share-1234-4567-78787',
            'size': 1,
            'share_id': 'share-1234-4567-78787',
            'share_proto': test_config.freenas_storage_protocol
        }
        snapshot = {'share': share, 'share_name': 'share-1234-4567-78787',
                    'name': 'share-snap-1234-4567'}
        snap_params = {}
        snap_params['name'] = FAKE_SNAPSHOT_NAME
        snap_params['dataset'] = ('%s/%s') % (test_config.freenas_dataset,
                                              FAKE_SHARE_NAME)
        snap_req = ('%s/') % (FreeNASServer.REST_API_SNAPSHOT)

        mock_rest_cmd.return_value = {'status': 'ok'}

        return_model = {'provider_location': '%s@%s' %
                        (self._get_share_path(),
                        FAKE_SNAPSHOT_NAME)
        }

        self.assertEqual(return_model,
                         self._driver.create_snapshot(self._ctx, snapshot))

        mock_rest_cmd.assert_called_with(FreeNASServer.CREATE_COMMAND,
                                         snap_req, json.dumps(snap_params))

    @patch.object(FreeNASServer, 'invoke_command')
    def test_create_snapshot_with_error(self, mock_rest_cmd):

        share = {
            'name': 'share-1234-4567-78787',
            'size': 1,
            'share_id': 'share-1234-4567-78787',
            'share_proto': test_config.freenas_storage_protocol
        }
        snapshot = {'share': share, 'share_name': 'share-1234-4567-78787',
                    'name': 'share-snap-1234-4567'}

        mock_rest_cmd.return_value = {'status': 'error',
                                      'response': 'unable to create snapshot'}

        self.assertRaises(FreeNASApiError,
                          self._driver.create_snapshot,
                          self._ctx, snapshot)

    @patch.object(FreeNASServer, 'invoke_command')
    def test_delete_snapshot(self, mock_rest_cmd):

        share = {
            'name': 'share-1234-4567-78787',
            'size': 1,
            'share_id': 'share-1234-4567-78787',
            'share_proto': test_config.freenas_storage_protocol
        }
        snapshot = {'share': share, 'share_name': 'share-1234-4567-78787',
                    'name': 'share-snap-1234-4567'}

        del_req = ('%s/%s/%s@%s/') % (FreeNASServer.REST_API_SNAPSHOT,
                                      test_config.freenas_dataset,
                                      FAKE_SHARE_NAME, FAKE_SNAPSHOT_NAME)

        mock_rest_cmd.return_value = {'status': 'ok'}
        self._driver.delete_snapshot(self._ctx, snapshot)

        mock_rest_cmd.assert_called_with(FreeNASServer.DELETE_COMMAND,
                                         del_req, None)

    @patch.object(FreeNASServer, 'invoke_command')
    def test_delete_snapshot_with_error(self, mock_rest_cmd):

        share = {
            'name': 'share-1234-4567-78787',
            'size': 1,
            'share_id': 'share-1234-4567-78787',
            'share_proto': test_config.freenas_storage_protocol
        }
        snapshot = {'share': share, 'share_name': 'share-1234-4567-78787',
                    'name': 'share-snap-1234-4567'}

        mock_rest_cmd.return_value = {'status': 'error',
                                      'response': 'unable to create snapshot'}

        self.assertRaises(FreeNASApiError,
                          self._driver.delete_snapshot,
                          self._ctx, snapshot)

    @patch.object(FreeNASServer, 'invoke_command')
    def test_create_share_from_snapshot(self, mock_rest_cmd):

        share = {
            'name': 'share-1234-4567-78787',
            'size': 1,
            'share_id': 'share-1234-4567-78787',
            'share_proto': test_config.freenas_storage_protocol
        }
        snapshot = {'share': share, 'share_name': 'share-1234-4567-78787',
                    'name': 'share-snap-1234-4567'}

        path = self._get_share_path()
        location = {'path': '%s:%s' % (test_config.freenas_server_hostname,
                                       path)}

        mock_rest_cmd.return_value = {'status': 'ok'}
        self.assertEqual([location],
                         self._driver.create_share_from_snapshot(
                         self._ctx, share, snapshot))

    @patch.object(FreeNASServer, 'invoke_command')
    def test_create_share_from_snapshot_with_error(self, mock_rest_cmd):

        share = {
            'name': 'share-1234-4567-78787',
            'size': 1,
            'share_id': 'share-1234-4567-78787',
            'share_proto': test_config.freenas_storage_protocol
        }
        snapshot = {'share': share, 'share_name': 'share-1234-4567-78787',
                    'name': 'share-snap-1234-4567'}

        mock_rest_cmd.return_value = {'status': 'error',
                                      'response': 'unable to create Share'}
        self.assertRaises(FreeNASApiError,
                          self._driver.create_share_from_snapshot,
                          self._ctx, share, snapshot)

    @patch.object(FreeNASProcessRequests, '_get_volume_stat')
    @patch('manila.share.driver.ShareDriver._update_share_stats')
    def test_update_share_stats(self, super_stats, mock_stats):
        mock_stats.return_value = (200, 150, 50)
        stats = {
            'vendor_name': 'FreeNAS',
            'storage_protocol': test_config.freenas_storage_protocol,
            'driver_version': '1.0',
            'share_backend_name': test_config.share_backend_name,
            'nfs_mount_point_base': test_config.freenas_mount_point_base,
            'pools': [{
                'pool_name': test_config.freenas_dataset,
                'total_capacity_gb': 200,
                'free_capacity_gb': 150,
                'snapshot_support': True,
                'create_share_from_snapshot_support': True,
                'reserved_percentage':
                    test_config.reserved_share_percentage,
                'compression': True,
                'dedupe': True,
                'thin_provisioning': test_config.freenas_thin_provisioning,
            }],
        }

        self._driver._update_share_stats()

        self.assertEqual(stats, self._driver._stats)
