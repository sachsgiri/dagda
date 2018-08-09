#
# Licensed to Dagda under one or more contributor
# license agreements. See the NOTICE file distributed with
# this work for additional information regarding copyright
# ownership. Dagda licenses this file to you under
# the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.
#

import json
import datetime
from flask import Blueprint
from exception.dagda_error import DagdaError
from log.dagda_logger import DagdaLogger
from api.internal.internal_server import InternalServer

# -- Global

check_api = Blueprint('check_api', __name__)


# Check docker by image name
@check_api.route('/v1/check/images/<path:image_name>', methods=['POST'])
def check_docker_by_image_name(image_name):
    # -- Check input
    if not image_name:
        return json.dumps({'err': 400, 'msg': 'Bad image name'}, sort_keys=True), 400

    # -- Docker pull from remote registry if it is necessary
    try:
        pulled = False
        if not InternalServer.get_docker_driver().is_docker_image(image_name):
            if ':' in image_name:
                tmp = image_name.split(':')[0]
                tag = image_name.split(':')[1]
                msg = 'Error: image library/' + image_name + ':' + tag + ' not found'
                output = InternalServer.get_docker_driver().docker_pull(tmp, tag=tag)
            else:
                msg = 'Error: image library/' + image_name + ':latest not found'
                output = InternalServer.get_docker_driver().docker_pull(image_name)
            if 'errorDetail' in output:
                DagdaLogger.get_logger().error(msg)
                raise DagdaError(msg)
            pulled = True
    except:
        return json.dumps({'err': 404, 'msg': 'Image name not found'}, sort_keys=True), 404

    # -- Process request
    data = {}
    data['image_name'] = image_name
    data['timestamp'] = datetime.datetime.now().timestamp()
    data['status'] = 'Analyzing'
    id = InternalServer.get_mongodb_driver().insert_docker_image_scan_result_to_history(data)
    InternalServer.get_dagda_edn().put({'msg': 'check_image', 'image_name': image_name, '_id': str(id),
                                        'pulled': pulled})

    # -- Return
    output = {}
    output['id'] = str(id)
    output['msg'] = 'Accepted the analysis of <' + image_name + '>'
    return json.dumps(output, sort_keys=True), 202


# Check docker by container id
@check_api.route('/v1/check/containers/<string:container_id>', methods=['POST'])
def check_docker_by_container_id(container_id):
    # -- Check input
    if not container_id:
        return json.dumps({'err': 400, 'msg': 'Bad container id'}, sort_keys=True), 400

    # -- Retrieves docker image name
    try:
        image_name = InternalServer.get_docker_driver().get_docker_image_name_by_container_id(container_id)
    except:
        return json.dumps({'err': 404, 'msg': 'Container Id not found'}, sort_keys=True), 404

    # -- Process request
    data = {}
    data['image_name'] = image_name
    data['timestamp'] = datetime.datetime.now().timestamp()
    data['status'] = 'Analyzing'
    id = InternalServer.get_mongodb_driver().insert_docker_image_scan_result_to_history(data)
    InternalServer.get_dagda_edn().put({'msg': 'check_container', 'container_id': container_id, '_id': str(id)})

    # -- Return
    output = {}
    output['id'] = str(id)
    output['msg'] = 'Accepted the analysis of <' + image_name + '> with id: ' + container_id
    return json.dumps(output, sort_keys=True), 202

# Check docker by name and version
@check_api.route('/v1/check/package/<string:package_name>/<string:package_version>', methods=['POST'])
@check_api.route('/v1/check/package/<string:package_name>', methods=['POST'])
def check_package_by_name_version(package_name, package_version=None):
    # -- Check input
    if not package_name and not package_version:
        return json.dumps({'err': 400, 'msg': 'Bad package_name '}, sort_keys=True), 400

    # -- Process request
    data = {}
    data['package_name'] = package_name
    if package_version:
        data['package_version'] = package_version
    data['timestamp'] = datetime.datetime.now().timestamp()
    data['status'] = 'Analyzing'
    id = InternalServer.get_mongodb_driver().insert_docker_image_scan_result_to_history(data)
    InternalServer.get_dagda_edn().put({'msg': 'check_package', 'package_name': package_name, 'package_version': package_version,'_id': str(id)})
    # -- Return
    output = {}
    output['id'] = str(id)
    output['msg'] = 'Accepted the analysis of <' + package_name + '> with version: ' + package_version
    return json.dumps(output, sort_keys=True), 202
