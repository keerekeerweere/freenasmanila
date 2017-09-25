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

from oslo_config import cfg

# This file contains configuration options for FreeNAS Manilla driver.

# FreeNAS appliance connection options
freenas_connection_opts = [
    cfg.StrOpt('freenas_server_hostname',
               default=None,
               help='Host name for the storage controller'),
    cfg.StrOpt('freenas_api_version',
               default='v1.0',
               help='FREENAS API version'),
    cfg.IntOpt('freenas_server_port',
               default=3000,
               help='Port number for the storage controller'),
    cfg.StrOpt('freenas_volume_backend_name',
               default='FREENAS_Storage',
               help='Backend Storage Controller Name'),
    cfg.StrOpt('freenas_vendor_name',
               default='FreeNAS',
               help='vendor name on Storage controller'),
    cfg.StrOpt('freenas_storage_protocol',
               default='NFS',
               help='storage protocol on Storage controller'),
    cfg.StrOpt('freenas_login',
               default='root',
               help='User name for the storage controller'),
    cfg.StrOpt('freenas_password',
               default='naruto',
               help='Password for the storage controller',
               secret=True), ]

# FreeNas appliance transport options
freenas_transport_opts = [
    cfg.StrOpt('freenas_transport_type',
               default='http',
               help='Transport type protocol'), ]

# FreeNAS appliance nfs related options
freenas_nfs_opts = [
    cfg.StrOpt('freenas_mount_point_base',
               default='/mnt',
               help='Base directory that contains NFS share mount points.'),
]

# FreeNAS zpool and dataset related options
freenas_dataset_opts = [
    cfg.StrOpt('freenas_dataset',
               default='agattivol',
               help='Parent folder on FreeNAS.'),
    cfg.StrOpt('freenas_dataset_compression',
               default='on',
               choices=['on', 'off', 'gzip', 'gzip-1', 'gzip-2', 'gzip-3',
                        'gzip-4', 'gzip-5', 'gzip-6', 'gzip-7', 'gzip-8',
                        'gzip-9', 'lzjb', 'zle', 'lz4'],
               help='Compression value for new ZFS folders.'),
    cfg.StrOpt('freenas_dataset_dedupe',
               default='off',
               choices=['on', 'off', 'inherit'],
               help='Deduplication value for new ZFS folders.'),
    cfg.BoolOpt('freenas_thin_provisioning',
                default=True,
                help=('If True shares will not be space guaranteed and '
                      'overprovisioning will be enabled.')),
]
