#!/usr/bin/env python
import logging
import argparse
import sys
import time
import json
import requests
from requests.packages.urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
#v3 from urllib.parse import urlsplit, parse_qs
from urlparse import urlparse, parse_qs
import subprocess
import threading

#logging config
logging.basicConfig(format='%(asctime)s %(levelname)-8s %(message)s',level=logging.INFO,datefmt='%Y-%m-%d %H:%M:%S')
logger = logging.getLogger(__name__)

#globals
MODULE = "env-create"
CONFIG_FILE = {"platform-1":"./platform-1.json"}

#app configuration
parser = argparse.ArgumentParser(description='create the basic cloud on-boarding environment')
parser.add_argument('--platform', choices=['platform-1'],help='the target platform ',required=True)
parser.add_argument('--tenant',help='the name of the tenant plus a random suffix/prefix',required=True)
parser.add_argument('--charts', nargs='*', help='specify a list of the charts you want to deploy', required=True)
parser.add_argument('--params', nargs='*', help='specify a list of the charts parameters you want to use', required=True)
parser.add_argument('--storage', choices=['local','glusterfs'],help='select the PV storage type ',required=False,default=argparse.SUPPRESS)


def get_config(filename):
    try:
        f = open(filename, 'r')
    except FileNotFoundError:
        logging.error("config file not found:{}".format(filename))
        sys.exit(1)
    else:
        return json.load(f)

def run_local_cmd_4_storage(storage_type,namespace,config):
    result = True
    commands = {"local":['kubectl', 'get', 'pv', '-n',namespace],"glusterfs":[ 'kubectl', 'apply', '-f', './rancher-gluster.yml','-n', namespace]}
    try:
        cmd_ouput = subprocess.Popen(commands[storage_type],
                             stdout=subprocess.PIPE,
                             stderr=subprocess.STDOUT)
    except Exception as e:
        logging.error("error running local cmd:{}".format(commands[storage_type]))
        sys.exit(1)
    else:
        logging.info("successfully run cmd:{}".format(commands[storage_type]))
        stdout, stderr = cmd_ouput.communicate()
        string_out = stdout.decode("utf-8")
        if stderr is not None:
            string_error = stderr.decode("utf-8")
        else:
            string_error = ""
        logging.debug("output:{} error:{}".format(string_out,string_error))
        if storage_type == "glusterfs" and "created" not in string_out:
            logging.error("error running cmd:{} output:{}".format(commands[storage_type],string_out))
            result = False
    return result



def get_deployment_url(config,app_object,namespace_name):
    _bearer = "Bearer " + str(config['bearer'])
    _headers = {'Content-Type': 'application/json', 'Authorization': _bearer}
    _url = app_object['catalog']
    #v3 query = urlsplit(_url).query
    #v3 params = parse_qs(query)
    parsed = urlparse(_url)
    params = parse_qs(parsed.query)
    logging.debug('catalog parameters {}'.format(params))
    _base_url = config['host'] + '/v3/project/' + config['projectid'] + '/workloads/deployment:' + namespace_name + ":"
    if config['rancherVersion'] == '2.2.1':
        _deployment_url = _base_url + app_object['name'] + "-" + params['template'][0]
    else:
        _deployment_url = _base_url + app_object['name']
    return _deployment_url


def get_parameters(chart,static_config,dynamic_parameters):
    logging.debug('static:{} dynamic:{}'.format(static_config,dynamic_parameters))
    result = {}
    if static_config and len(static_config) > 0:
        result.update(static_config)
    else:
        logging.info('no static chart custom answers for chart:{}'.format(chart))
    for parameter in dynamic_parameters:
        if chart in parameter:
            _clean_param = parameter.split('.',1)[1]
            key,value = _clean_param.split("=")
            logging.info('adding parameter:{} value:{} to chart:{}'.format(key,value,chart))
            result[key] = value
    return result


def poll_url(config,url,delay,key,expected_value):
    _retries = 4
    _bearer = "Bearer " + str(config['bearer'])
    _headers = {'Content-Type': 'application/json', 'Authorization': _bearer}
    for _count in range(0,_retries):
        try:
            r = requests.get(url, headers=_headers, verify=False, timeout=delay)
        except Exception as e:
            logging.warning("error {}.poll_url error:{}".format(MODULE, e))
            sys.exit(1)
        else:
            if r.status_code == 200:
                j_data = json.loads(r.text)
                logging.debug(j_data)
                if j_data[key] == expected_value:
                    logging.debug("poll {} for {}={} successful".format(url,key,expected_value))
                    return True
        time.sleep(delay)
    logging.error("poll failed for {} for {}={}".format(url,key,expected_value))
    sys.exit(1)


def create_tenant_namespace(config,tenantname):
    _url = config['host'] + '/v3/cluster/' + config['clusterid'] + '/namespaces/'
    _bearer = "Bearer " + str(config['bearer'])
    _headers = {'Content-Type': 'application/json', 'Authorization': _bearer}
    _data = {"name":tenantname,"description":"default namespace for tenant","projectId":config['projectid'],"containerDefaultResourceLimit":config['containerLimits']}
    logging.debug("connecting to {} with payload:{}".format(_url,_data))
    try:
        r = requests.post(_url, data=json.dumps(_data), headers=_headers,verify=False,timeout=2.0)
    except requests.ConnectionError as conn_e:
        logging.error("error in {}.create_tenant_namespace connection error, host:{}".format(MODULE, _url))
        sys.exit(1)
    except Exception as e:
        logging.error("error in {}.create_tenant_namespace error:{}".format(MODULE, e))
        sys.exit(1)
    else:
        result = {}
        if r.status_code == 201:
            j_data = json.loads(r.text)
            logging.debug(j_data)
            result['name'] = j_data['name']
            result['status'] = j_data['state']
            result['self_link'] = j_data['links']['self']
            return result
        elif r.status_code == 409:
            logging.error("error:{} namespace resource exists".format(r.status_code))
            sys.exit(1)
        else:
            logging.info("error connecting to {}, error code:{} response:{}".format(_url, r.status_code, json.loads(r.text)))
            sys.exit(1)



def create_tenant_volume(config,tenantname,namespace_name,type,chart,chart_index):
    _url = config['host'] + '/v3/cluster/' + config['clusterid'] + '/persistentVolumes/'
    _bearer = "Bearer " + str(config['bearer'])
    _headers = {'Content-Type': 'application/json', 'Authorization': _bearer}
    claim_name = chart + '-claim'
    claim_ref = {"namespace":namespace_name,"name":claim_name}
    _data = {"name":chart+"-pv","description":"default volume for chart","projectId":config['projectid'],
             "namespace":namespace_name,"capacity":{"storage":config['volumeStorage']},"accessModes":config['accessModes'],
             "projectId":config['projectid'],"claimRef":claim_ref}
    _data[type] = config[type]
    if type == 'local':
        storage_path = _data[type]['path'] + "vol" + str(chart_index)
        _data['nodeAffinity'] = config['nodeAffinity']
        _data[type]['path'] = storage_path
    logging.debug("connecting to {} with payload:{}".format(_url,_data))
    try:
        r = requests.post(_url, data=json.dumps(_data), headers=_headers,verify=False,timeout=2.0)
    except requests.ConnectionError as conn_e:
        logging.error("error in {}.create_tenant_volume connection error, host:{}".format(MODULE, _url))
        sys.exit(1)
    except Exception as e:
        logging.error("error in {}.create_tenant_volume error:{}".format(MODULE, e))
        sys.exit(1)
    else:
        result = {}
        cmd_result_ok = run_local_cmd_4_storage(type,namespace_name,config)
        if cmd_result_ok:
            if r.status_code == 201:
                j_data = json.loads(r.text)
                logging.debug(j_data)
                result['name'] = j_data['name']
                result['status'] = j_data['state']
                result['self_link'] = j_data['links']['self']
                return result
            elif r.status_code == 409:
                logging.error("error:{} volume resource exists".format(r.status_code))
                sys.exit(1)
            else:
                logging.info("error connecting to {}, error code:{} response:{}".format(_url,r.status_code,json.loads(r.text)))
                sys.exit(1)
        else:
            logging.info("error running local storage command for storage:{}".format(type))
            sys.exit(1)

def create_tenant_volume_claim(config,tenantname,namespace_name,chart):
    _url = config['host'] + '/v3/project/' + config['projectid'] + '/persistentVolumeClaims/'
    _bearer = "Bearer " + str(config['bearer'])
    _headers = {'Content-Type': 'application/json', 'Authorization': _bearer}
    _data = {"name":chart+"-claim","description":"default volume claim for pipeline","namespaceId":namespace_name,
             "resources":{"requests":{"storage":config['claimStorage']}},"accessModes":config['accessModes'],
             "projectId":config['projectid']}
    logging.debug("connecting to {} with payload:{}".format(_url,_data))
    try:
        r = requests.post(_url, data=json.dumps(_data), headers=_headers,verify=False,timeout=2.0)
    except requests.ConnectionError as conn_e:
        logging.error("error in {}.create_tenant_volume_claim connection error, host:{}".format(MODULE, _url))
        sys.exit(1)
    except Exception as e:
        logging.error("error in {}.create_tenant_volume_claim error:{}".format(MODULE, e))
        sys.exit(1)
    else:
        result = {}
        if r.status_code == 201:
            j_data = json.loads(r.text)
            logging.debug(j_data)
            result['name'] = j_data['name']
            result['status'] = j_data['state']
            result['self_link'] = j_data['links']['self']
            return result
        elif r.status_code == 409:
            logging.error("error:{} volume claim resource exists".format(r.status_code))
            sys.exit(1)
        else:
            logging.info("error connecting to {}, error code:{} response:{}".format(_url,r.status_code,json.loads(r.text)))
            sys.exit(1)

def create_charts(config,tenantname,chart,namespace_name,paramters):
    _url = config['host'] + '/v3/project/' + config['projectid'] + '/apps/'
    _bearer = "Bearer " + str(config['bearer'])
    _headers = {'Content-Type': 'application/json', 'Authorization': _bearer}
    _chart_map = config['charts']
    result = {}
    if chart is not None and chart in _chart_map.keys():
        _data = {"name": tenantname + "-" + _chart_map[chart]['name'],
        "targetNamespace": namespace_name,
        "externalId": _chart_map[chart]['catalog'],
        "description": "application from "+_chart_map[chart]['description']}
        _data['answers'] = get_parameters(chart,_chart_map[chart]['answers'],paramters)
        try:
            r = requests.post(_url, data=json.dumps(_data), headers=_headers, verify=False, timeout=2.0)
        except requests.ConnectionError as conn_e:
            logging.error("error in {}.create_charts connection error, host:{}".format(MODULE, _url))
            sys.exit(1)
        except Exception as e:
            logging.error("error in {}.create_charts error:{}".format(MODULE, e))
            sys.exit(1)
        else:
            if r.status_code == 201:
                j_data = json.loads(r.text)
                logging.debug(json.dumps(j_data))
                result['name'] = j_data['name']
                result['status'] = j_data['state']
                result['self_link'] = j_data['links']['self']
                result['catalog'] = _chart_map[chart]['catalog']
                result['chart'] = chart
            elif r.status_code == 409:
                logging.error("error:{} chart resource exists".format(r.status_code))
                sys.exit(1)
            else:
                logging.info("error connecting to {}, error code:{} response:{}".format(_url, r.status_code,json.loads(r.text)))
                sys.exit(1)
    else:
            logging.warning("chart:{} not in mapper".format(chart))
            sys.exit(1)
    return result

def create_ingress(config,tenantname,chart,namespace_name,deployment_url):
    _url = config['host'] + '/v3/project/' + config['projectid'] + '/ingresses/'
    _bearer = "Bearer " + str(config['bearer'])
    _headers = {'Content-Type': 'application/json', 'Authorization': _bearer}
    _chart_map = config['charts']
    if "ingress" in _chart_map[chart] and len(_chart_map[chart]['ingress']) > 0:
        url_path, deployment_name = deployment_url.split("deployment:")
        _workloadIds = "deployment:"+deployment_name
        _paths = {"path":"/"+tenantname,"targetPort":_chart_map[chart]['ingress']['targetPort'],"workloadIds":[_workloadIds]}
        _rules = {"host":_chart_map[chart]['ingress']['hostname'],"paths":[_paths]}
        _data = {"name": tenantname + chart, "description": chart +"-ingress", "namespaceId": namespace_name,"projectId": config['projectid'],"rules":[_rules]}
        logging.debug("connecting to {} with payload:{}".format(_url, json.dumps(_data)))
        try:
            r = requests.post(_url, data=json.dumps(_data), headers=_headers,verify=False,timeout=2.0)
        except requests.ConnectionError as conn_e:
            logging.error("error in {}.create_ingress connection error, host:{}".format(MODULE, _url))
            sys.exit(1)
        except Exception as e:
            logging.error("error in {}.create_ingress error:{}".format(MODULE, e))
            sys.exit(1)
        else:
            result = {}
            if r.status_code == 201:
                j_data = json.loads(r.text)
                logging.debug(j_data)
                result['name'] = j_data['name']
                result['status'] = j_data['state']
                result['self_link'] = j_data['links']['self']
                return result
            elif r.status_code == 409:
                logging.error("error:{} ingress resource exists".format(r.status_code))
                sys.exit(1)
            else:
                logging.info("error connecting to {}, error code:{} response:{}".format(_url, r.status_code, json.loads(r.text)))
                sys.exit(1)
    return {"self_link":"na"}


def deploy_app_and_ingress(config,tenant,chart,namespace,params):
    app_object = create_charts(config, tenant, chart, namespace, params)
    if poll_url(config, app_object['self_link'], 10, 'state', 'active'):
        deployment_url = get_deployment_url(config, app_object, namespace)
        logging.info('using deployment url:{}'.format(deployment_url))
        logging.info('successfully deployed app:{} '.format(app_object['self_link']))
        if poll_url(config, deployment_url, 60, 'state', 'active'):
            logging.info('successfully deployed workload:{} '.format(deployment_url))
            ingress_object = create_ingress(config, tenant, chart, namespace, deployment_url)
            if ingress_object['self_link'] != "na":
                if poll_url(config, ingress_object['self_link'], 20, 'state', 'active'):
                    logging.info('successfully created ingress:{} '.format(ingress_object['self_link']))
            return deployment_url
    return

def run_threads(config,tenant,charts,namespace,params):
    results = []
    for count in range(0,len(charts)):
        logging.info("creating thread for chart:{}".format(charts[count]))
        t = threading.Thread(target=deploy_app_and_ingress, args=(config,tenant,charts[count],namespace,params))
        t.start()
        results.append(t)
    return results



def main():
    print("Running {}".format(MODULE))
    chart_index = 0
    args = parser.parse_args()
    logging.info("platform:{} charts:{} parameters:{}".format(args.platform,args.charts,args.params))
    config = get_config(CONFIG_FILE[args.platform])
    namespace_object = create_tenant_namespace(config,args.tenant)
    if poll_url(config,namespace_object['self_link'],5,'state','active'):
        logging.info('successfully created namespace:{}'.format(namespace_object['self_link']))
        if "storage" in args:
            for chart in args.charts:
                volume_object = create_tenant_volume(config,args.tenant,namespace_object['name'],args.storage,chart,chart_index)
                if poll_url(config,volume_object['self_link'],5,'state','available'):
                    logging.info('successfully created volume:{}'.format(volume_object['self_link']))
                    volumeClaim_object = create_tenant_volume_claim(config,args.tenant,namespace_object['name'],chart)
                    if poll_url(config, volumeClaim_object['self_link'], 5, 'state', 'bound'):
                        logging.info('successfully created volume claim:{}'.format(volumeClaim_object['self_link']))
        thread_list = run_threads(config,args.tenant,args.charts,namespace_object['name'],args.params)
        for thread in thread_list:
                thread.join()
                logging.info('Thread:{}'.format(thread))
    sys.exit(0)


if __name__ == "__main__":
    main()
