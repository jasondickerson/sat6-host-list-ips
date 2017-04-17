#!/usr/bin/python
import sys
import os
import base64
from ConfigParser import SafeConfigParser

try:
    import requests
except ImportError:
    print "Please install the python-requests module."
    sys.exit(-1)

config_file = os.path.dirname(os.path.abspath(__file__)) + '/list_host_ips.cfg'

good_config = True
if os.path.isfile(config_file):
    config = SafeConfigParser()
    try:
        config.read(config_file)
    except:
        print 'Bad Configuration File.'
        good_config = False
        sys.exit(1)

    if config.has_section('authentication'):
        if config.has_option('authentication', 'satellite_list'):
            satellite_list = config.get('authentication', 'satellite_list').split(',')
        else:
            print 'Configuration section:  authentication.  satellite_list option is missing.'
            good_config = False
        if config.has_option('authentication', 'username'):
            username = config.get('authentication', 'username')
        else:
            print 'Configuration section:  authentication.  username option is missing.'
            good_config = False
        if config.has_option('authentication', 'password_b64'):
            password = base64.b64decode(config.get('authentication', 'password_b64'))
        else:
            print 'Configuration section:  authentication.  password_b64 is missing.'
            good_config = False
    else:
        print 'Configuration file is missing authentication section.'
        good_config = False

else:
    print 'Configuration File Missing.'

if not good_config:
    sys.exit(1)

def get_certificate(satellite):
    if not os.path.isfile(os.path.dirname(os.path.abspath(__file__)) + '/' + satellite + '.crt'):
        # Performs a GET using the passed URL location
        try:
            r = requests.get('http://' + satellite + '/pub/katello-server-ca.crt', auth=(username, password))
        except:
            print 'Certificate pull error.'
            sys.exit(1)
        if r and r.text:
            with open(os.path.dirname(os.path.abspath(__file__)) + '/' + satellite + '.crt', 'w') as certificate_file:
                certificate_file.write(r.text)
        else:
            print 'Certificate pull error.'
            sys.exit(1)

def get_json(url):
    # Performs a GET using the passed URL location
    try:
        r = requests.get(url, auth=(username, password), verify=os.path.dirname(os.path.abspath(__file__)) + '/' + url.split('/')[2] + '.crt')
    except:
        print 'API connection Error.'
        sys.exit(1)
    if r and r.json():
        if  'error' in r.json() and r.json()['error']:
            print 'Error:  ' + r.json()['error']['message']
            return []
        else:
            return r.json()
    else:
        return []

def get_api_version(satellite):
    api_status_url = 'https://' + satellite + '/api/status'
    api_status = get_json(api_status_url)
    if api_status and 'api_version' in api_status and (api_status['api_version'] == 1 or api_status['api_version'] == 2):
        return api_status['api_version']
    else:
        print 'Invalid API version.'
        sys.exit(2)

def get_results(url,params):
    per_page = 100
    results_list = []
    results_list_page = []
    page = 0
    while page == 0 or (int(results_list_page['per_page']) == len(results_list_page['results'])):
        page += 1
        # print url + '?per_page=' + str(per_page) + '&page=' + str(page)
        results_list_page = get_json(url + '?per_page=' + str(per_page) + '&page=' + str(page) + params)
        if results_list_page and 'results' in results_list_page:
            results_list += results_list_page['results']
        # print 'Page ' + str(page) + ' completed.'
        if not 'per_page' in results_list_page or not results_list_page['per_page']:
            break
    return results_list

def main():
    for satellite in satellite_list:
        get_certificate(satellite)
        api_version = get_api_version(satellite)

        if api_version == 1:
            print "API version 2 required.  Skipping " + satellite + "..."
            break
        else:
            foreman_host_list_url = 'https://' + satellite + '/api/v2/hosts'
            host_list = get_results(foreman_host_list_url,'&search=os=RedHat')
            for host in host_list:
                print host['name'] + ',' + host['ip']

if __name__ == "__main__":
    main()

# vim: set ts=4 sw=4 sts=4 et :
# syntax=off :
