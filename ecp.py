#!/usr/bin/env python3

from __future__ import print_function
import requests
import sys
import os
import argparse
import json
import getpass
import datetime
import yaml

def get_depl_status(depl, headers):
  return requests.get(depl['_links']['status']['href'], headers=headers).json()

def prettyprint(resp, res, headers):
  table = []
  if res == 'deployment' or res == 'deployments':
    if '_embedded' in resp:
      table.append(['REFERENCE','APP NAME', 'STARTED', 'STATUS'])
      for depl in resp['_embedded']['deploymentResourceList']:
        if 'startedTime' in depl:
          ts = depl['startedTime'] / 1000.0
          start_t = datetime.datetime.fromtimestamp(ts).strftime('%H:%M %d-%m-%Y')
        else:
          start_t = ''
      
        status_r = get_depl_status(depl, headers)
        try:
          status = status_r['status']
        except:
          status = 'Error getting status'

        table.append([depl['reference'], depl['applicationName'], start_t, status])

  if res == 'app' or res == 'apps':
    if '_embedded' in resp:
      table.append(['NAME', 'VERSION'])
      for app in resp['_embedded']['applicationResourceList']:
        table.append([app['name'], app['version']])

  if res == 'config' or res == 'configs':
    if '_embedded' in resp:
      for config in resp['_embedded']['configurationResourceList']:
        print('- '+config['name']+':')
        print('    Cloud provider parameters: '+config['cloudProviderParametersName'])
        print('    SSH Public Key: '+config['sshKey'])
        print('    Parameters: '+config['deploymentParametersName'])
      return

  if res == 'cred' or res == 'creds':
    if '_embedded' in resp:
      for cred in resp['_embedded']['cloudProviderParametersResourceList']:
        print('- '+cred['name']+':')
        print('    Provider: '+cred['cloudProvider'])
        print('    Parameters: ')
        for field in cred['fields']:
          print('    * '+field['key']+': '+field['value'])
      return

  if res == 'param' or res == 'params':
    if '_embedded' in resp:
      for param in resp['_embedded']['configurationDeploymentParametersResourceList']:
        print('- '+param['name']+':')
        print('    Parameters: ')
        for field in param['fields']:
          print('    * '+field['key']+': '+field['value'])
      return

  if len(table) > 0:
    print_table(table)
  else:
    # For individual requests, dump to yaml which is better readable
    print(yaml.safe_dump(resp, indent=2, default_flow_style=False))
        
def print_table(table):
  col_width = max([max(len(str(x)) for x in col) for col in zip(*table)]) + 2
  # assuming square table, can take length of first row
  row_format = len(table[0]) * '{:<{fill}}'    
  for row in table:
    print(row_format.format(*row, fill=col_width))

def geturl(res, name):
  baseurl = 'https://api.portal.tsi.ebi.ac.uk'
  if res == 'cred' or res == 'creds':
    respath = '/cloudproviderparameters/'
  elif res == 'param' or res == 'params':
    respath = '/configuration/deploymentparameters/'
  elif res == 'config' or res == 'configs':
    respath = '/configuration/'
  elif res == 'app' or res == 'apps':
    respath = '/application/'
  elif res == 'deployment' or res == 'deployments':
    respath = '/deployment/'
  elif res == 'logs':
    return baseurl+'/deployment/'+name+'/logs'
  elif res == 'destroylogs':
    return baseurl+'/deployment/'+name+'/destroylogs'
  elif res == 'status':
    return baseurl+'/deployment/'+name+'/status'

  try:
    return baseurl+respath+name
  except UnboundLocalError:
    print('Unknown verb or resource, try --help for usage', file=sys.stderr)

def get_token(tokenfile):
  if tokenfile is not None:
    with open(args.token, 'r') as tokenfile:
      token = tokenfile.read().replace('\n','')
  elif "ECP_TOKEN" in os.environ:
    token = os.environ["ECP_TOKEN"]
  elif os.path.isfile(os.environ['HOME']+'/.ecp_token'):
    with open(os.environ['HOME']+'/.ecp_token', 'r') as tokenfile:
      token = tokenfile.read().replace('\n','')
  else:
    token = ''

  return token

def login(user='', pw=''):
  if user == '':
    user = input('Please enter your username: ')
  if pw == '':
    pw   = getpass.getpass(prompt = 'Please enter your password: ')
  response = requests.get('https://api.aai.ebi.ac.uk/auth', auth=(user,pw))
  with open(os.environ['HOME']+'/.ecp_token', 'w') as tokenfile:
    print(response.text, file=tokenfile)

  return response.text

def make_request(url, verb, headers, datafile=''):
  if verb == 'get':
    response = requests.get(url, headers=headers)
  elif verb == 'create':
    with open(datafile, 'r') as json_file:
      response = requests.post(url, headers=headers, data = json_file.read())
  elif verb == 'delete':
    response = requests.delete(url, headers=headers)
  elif verb == 'stop':
    response = requests.put(url+'/stop', headers=headers)
  elif verb == 'login':
    response = login()
  else:
    response = '{}'
    print('Unknown verb, try --help for usage')

  return response

def print_request(response, verb, resource, headers, jsondump):
  try:
    r_json = response.json()
  except:
    #print("Could not decode, raw response:")
    try:
      print(response.text)
    except AttributeError:
      print(response)
      
    return

  if jsondump:
    print(json.dumps(r_json, indent=2))
    return

  if verb == 'get':
    prettyprint(response.json(), resource, headers)
  else:
    # fallback to yaml as it is more readable by humans
    print(yaml.safe_dump(response.json(), indent=2, default_flow_style=False))
  
def main(argv):
  parser = argparse.ArgumentParser(description='EBI CLoud Portal CLI')
  parser.add_argument('verb', help='Action to perform on resource, one of: get/create/delete/stop(deployments only)/login')
  parser.add_argument('resource', nargs='?', help='Resource type to perform action on, one of: cred/param/config/app/deployment/logs/status')
  parser.add_argument('name', nargs='?', help='Resource name to perform action on; can be omitted for \'get\' action to list all', default='')
  parser.add_argument('--file', '-f', help='File containing JSON to post')
  parser.add_argument('--token', '-t', help='File containing JWT identity token, is sourced from ECP_TOKEN env var by default')
  parser.add_argument('--json', '-j', help='Print raw JSON responses', action='store_true')
  parser.add_argument('--user', '-u', help='Username for login action', default='')
  parser.add_argument('--password', '-p', help='Password for login action', default='')

  args=parser.parse_args()
  token = get_token(args.token)

  headers = {'Authorization': 'Bearer '+token, 'Content-Type': 'application/json'}

  if args.verb == 'login':
    r = login(args.user, args.password)
    print_request(r, args.verb, args.resource, headers, args.json)
    return
  else:
    url = geturl(args.resource, args.name)
    # something went wrong, error is printed higher up so just exit
    if url is None:
      return

  r = make_request(url, args.verb, headers, datafile=args.file)
  print_request(r, args.verb, args.resource, headers, args.json)

if __name__ == "__main__":
  main(sys.argv)
