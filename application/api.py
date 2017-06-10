# -*- coding: utf-8 -*-
from flask import abort, Blueprint, jsonify, make_response, request

from application import app
from application.modules.app_manager import AppManager
from application.modules.db_manager import DBManager
from application.modules.file_io import FileIO
from application.modules.machines_cache import MachinesCache
from application.modules.users import UserObj
from application.modules.validation import Validation

api = Blueprint('api', __name__)
machines_cache = MachinesCache.get_current_instance()
mongo = DBManager.get_current_instance()

# Expose each machine's data via REST API
# eg. curl -i http://localhost:5000/api/machines/vm01
# eg. curl -i http://localhost:5000/api/machines/172.30.0.1
@api.route('/api/machines/<hostname>', methods=['GET'])
def get_machine_api(hostname):
    doc = None
    if machines_cache.get(hostname) in machines_cache.machine_obj_list:
        doc = machines_cache.convert_machine_to_doc(hostname)
    else:
        if Validation.is_valid_ipv4(hostname):
            machine = mongo.find_one({'ip_address': hostname})
        else:
            machine = mongo.find_one({'hostname': hostname})

        if machine:
            doc = machine.to_mongo().to_dict()
            doc.pop('_id')      # remove '_id' field
    if doc:
        return jsonify(data=doc)

    abort(404)


# Expose all machines' data via REST API
# eg. curl -i http://localhost:5000/api/machines/all
@api.route('/api/machines', methods=['GET'])
@api.route('/api/machines/all', methods=['GET'])
def get_all_api():
    if machines_cache.get():
        docs = machines_cache.convert_machine_to_doc()
    else:
        machines = mongo.find({}).order_by('hostname', 'ip_address_decimal')
        docs = [machine.to_mongo().to_dict() for machine in machines if machine['hostname'] != '#Unknown']
        [doc.pop('_id') for doc in docs]    # remove '_id' field
    # return all machines except Hostname = #Unknown
    if docs:
        return jsonify(data=docs)
    abort(404)


# Add machines via RESTful API
# eg. curl -H "Content-Type: application/json" -X "POST" http://localhost:5000/api/machines/add/1.1.1.1:ubuntu
@api.route('/api/machines/add/<ipaddr>:<username>', defaults={'password': None}, methods=['POST'])
@api.route('/api/machines/add/<ipaddr>:<username>:<password>', methods=['POST'])
def register_machine_api_01(ipaddr, username, password):
    error_list = []

    # validate ip address format and duplication check
    is_duplicate = FileIO.exists_in_file(ipaddr)
    is_valid_ipaddr = Validation.is_valid_ipv4(ipaddr)
    is_valid_username = Validation.is_valid_username(username)
    is_valid_password = Validation.is_valid_password(password)

    if not is_valid_ipaddr:
        error_list.append("invalid ip address")
    if not is_valid_username:
        error_list.append("invalid username")
    if not is_valid_password:
        error_list.append("invalid password")
    if is_duplicate:     # IP Address already exists in the login file
        error_list.append("ip duplicate")

    # validation = all OK
    elif (not is_duplicate) and is_valid_ipaddr and is_valid_username and is_valid_password:
        if AppManager.add_machine(ipaddr, username, password):
            app.logger.info("- ADDED - %s", ipaddr)
            return make_response(jsonify(result={'success': True, 'added machines': 1}), 201)
    return make_response(jsonify(result={'success': False, 'reason': error_list}), 422)


# Add machines via RESTful API (by using -d option)
## eg. curl -H "Content-Type: application/json" -X "POST" http://localhost:5000/api/machines/add -d '[{"IP Address": "1.1.1.1", "Username": "ubuntu", "Password": "test"}, {"IP Address": "2.2.2.2", "Username": "ubuntu"}]'
@api.route('/api/machines/add', methods=['POST'])
def register_machine_api_02():
    if not request.get_json():
        abort(400)

    add_machines = request.get_json()
    if not isinstance(add_machines, list):
        add_machines = [add_machines]

    errors = {}
    all_success = True

    for item in add_machines:
        ipaddr = item['IP Address']
        username = item['Username']
        try:
            password = item['Password']
        except:
            password = None

        errors[ipaddr] = []

        # validate ip address format and duplication check
        is_duplicate = FileIO.exists_in_file(ipaddr)
        is_valid_ipaddr = Validation.is_valid_ipv4(ipaddr)
        is_valid_username = Validation.is_valid_username(username)
        is_valid_password = Validation.is_valid_password(password)

        if not is_valid_ipaddr:
            errors[ipaddr].append("invalid ip address")
        if not is_valid_username:
            errors[ipaddr].append("invalid username")
        if not is_valid_password:
            errors[ipaddr].append("invalid password")
        if is_duplicate:     # IP Address already exists in the login file
            errors[ipaddr].append("ip duplicate")

        # validation = all OK
        elif (not is_duplicate) and is_valid_ipaddr and is_valid_username and is_valid_password:
            errors.pop(ipaddr, None)
            if AppManager.add_machine(ipaddr, username, password):
                app.logger.info("- ADDED - %s", ipaddr)
                continue

        all_success = False

    if all_success:
        return make_response(jsonify(result={'success': True, 'added machines': len(add_machines)}), 201)
    return make_response(jsonify(result={'success': False, 'reason': errors}), 422)


# Delete machines via RESTful API
# eg. curl -H "Content-Type: application/json" -X "DELETE" http://localhost:5000/api/machines/delete/1.1.1.1
@api.route('/api/machines/delete/<ipaddresses>', methods=['DELETE'])
def delete_machine_api_01(ipaddresses):
    del_list = [x for x in ipaddresses.split(",") if FileIO.exists_in_file(x)]
    del_result = AppManager.del_machine(del_list)
    if del_result > 0:
        del_ip_list = ", ".join([ip for ip in del_list])
        app.logger.info("- DELETED - %s", del_ip_list)
        return jsonify(result={'success': True, 'deleted machines': del_result})
    return make_response(jsonify(result={'success': False, 'deleted machines': del_result}), 422)


# Delete machines via RESTful API (by using -d option)
# eg. curl -H "Content-Type: application/json" -X "DELETE" http://localhost:5000/api/machines/delete -d '{"IP Address": [ "1.1.1.1", "2.2.2.2", "3.3.3.3" ]}'
@api.route('/api/machines/delete', methods=['DELETE'])
def delete_machine_api_02():
    if not request.get_json() or not 'IP Address' in request.get_json():
        abort(400)
    del_list = request.get_json()['IP Address']

    # convert to list if the data is not
    if not isinstance(del_list, list):
        del_list = del_list.split()

    # filter ip addresses which are not in text file
    del_list = [x for x in del_list if FileIO.exists_in_file(x)]

    del_result = AppManager.del_machine(del_list)
    if del_result > 0:
        del_ip_list = ", ".join([ip for ip in del_list])
        app.logger.info("- DELETED - %s", del_ip_list)
        return jsonify(result={'success': True, 'deleted machines': del_result})
    return make_response(jsonify(result={'success': False, 'deleted machines': del_result}), 422)


# for tests only
@app.route('/api/users/add', methods=['POST'])
def add_user_api():
    if not request.get_json():
        abort(400)

    username = request.get_json()['Username']
    password = request.get_json()['Password']

    if mongo.find_user(username):
        return make_response(jsonify(result={'success': False, 'error': "User already exists"}), 422)
    else:
        hash_password = UserObj.hash_password(password)
        mongo.add_user(username, hash_password)
        app.logger.warning("- ADDED ACCOUNT - %s", username)
        return jsonify(result={'success': True, 'added_users': 1})


# for tests only
@api.route('/api/users/delete/<username>', methods=['DELETE'])
def delete_user_api(username):
    del_result = mongo.delete_user(username)
    if del_result > 0:
        app.logger.warning("- DELETED ACCOUNT - %s", username)
        return jsonify(result={'success': True, 'deleted users': del_result})
    return make_response(jsonify(result={'success': False, 'deleted users': del_result}), 422)


@app.errorhandler(404)
def not_found(error):
    return make_response(jsonify(result={'error': error.description}), 404)


@app.errorhandler(400)
def bad_request(error):
    return make_response(jsonify(result={'error': error.description}), 400)


@app.errorhandler(405)
def not_allowed(error):
    return make_response(jsonify(result={'error': error.description}), 405)
