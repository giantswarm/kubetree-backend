# coding: utf8

from flask import abort
from flask import Flask
from flask import json
from flask import jsonify
import logging
import os
import requests

app = Flask(__name__)

token = None

app.config.update(dict(
    KUBERNETES_SERVICE_HOST = os.getenv("KUBERNETES_SERVICE_HOST")
))

class ApiException(Exception):
    status_code = 400
    def __init__(self, message, status_code=None, error_id=None, payload=None):
        Exception.__init__(self)
        self.message = message
        if status_code is not None:
            self.status_code = status_code
        self.payload = payload
        self.error_id = error_id
    def to_dict(self):
        rv = dict(self.payload or ())
        rv["message"] = self.message
        if self.error_id:
            rv["error_id"] = self.error_id
        return rv

@app.errorhandler(ApiException)
def handle_api_exception(error):
    response = jsonify(error.to_dict())
    response.status_code = error.status_code
    return response


@app.errorhandler(500)
def server_error_handler(e):
    return jsonify(message=str(e)), 500


@app.errorhandler(404)
def not_found_handler(e):
    return jsonify(message=str(e)), 404


def get_default_token():
    """
    Returns the value of the default auth token
    """
    path = "/var/run/secrets/kubernetes.io/serviceaccount/token"
    with open(path, "rb") as tokenfile:
        token = tokenfile.read()
    return token.strip()


def get_containers(token):
    """
    Return information from k8s API
    """
    uri = "https://%s/api/v1/pods" % app.config["KUBERNETES_SERVICE_HOST"]
    headers = {
        "Authorization": "Bearer %s" % token
    }
    r = requests.get(uri, headers=headers, verify=False)
    r.raise_for_status()
    data = r.json()
    # collect sparse data to return
    containers = []
    for pod in data["items"]:
        if "status" not in pod:
            continue
        # skip Jobs which are no longer running
        if "phase" in pod["status"] and pod["status"]["phase"] in ("Failed", "Succeeded"):
            continue
        if "containerStatuses" not in pod["status"]:
            continue
        for cont in pod["status"]["containerStatuses"]:
            if "containerID" not in cont:
                continue
            record = {
                "id": cont["containerID"],
                "name": cont["name"],
                "image": cont["image"],
                "image_hash": cont["imageID"],
                "pod_name": pod["metadata"]["name"],
                "pod_uid": pod["metadata"]["uid"],
                "namespace": pod["metadata"]["namespace"],
                "node_name": pod["spec"]["nodeName"],
            }
            containers.append(record)
    return containers


def get_container_ram_usage(ns, pod, container):
    uri_template = "http://heapster.kube-system.svc/api/v1/model/namespaces/{ns}/pods/{pod}/containers/{container}/metrics/memory/usage/"
    uri = uri_template.format(ns=ns, pod=pod, container=container)
    r = requests.get(uri)
    r.raise_for_status()
    data = r.json()
    # return most recent value
    if r.status_code != 200:
        return None
    if "metrics" not in data:
        return None
    if len(data["metrics"]) == 0:
        return None
    if "value" not in data["metrics"][-1]:
        return None
    return data["metrics"][-1]["value"]


@app.route("/")
def index():
    """
    Return all info in one big list
    """
    containers = get_containers(token)
    for n in range(len(containers)):
        containers[n]["ram_usage"] = get_container_ram_usage(
            ns=containers[n]["namespace"],
            pod=containers[n]["pod_name"],
            container=containers[n]["name"])
    return jsonify(containers)


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    token = get_default_token()
    if os.getenv("DEBUGGING") is None:
        app.run(debug=False, host="0.0.0.0", port=5000)
    else:
        app.run(debug=True, host="0.0.0.0", port=5000)


