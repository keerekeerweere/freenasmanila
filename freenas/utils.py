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


# Helper utility module for freenas manila driver.
def get_size_in_gb(size_in_bytes):
    "convert size in gbss"
    return size_in_bytes/(1024*1024*1024)


def generate_share_name(name, mntpoint):
    """Create FreeNAS volume / share name mapping"""
    backend_share = 'agtshare-' + name.split('-')[1]
    backend_mntpnt = mntpoint + "/" + backend_share
    return {'name': backend_share, 'mountpoint': backend_mntpnt}


def generate_snapshot_name(name):
    """Create FREENAS snapshot name. """
    snap_name = 'agtsnap-' + name.split('-')[2]
    return snap_name
