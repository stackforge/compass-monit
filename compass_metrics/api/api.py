# Copyright 2014 Huawei Technologies Co. Ltd
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Define all the RestfulAPI entry points."""
import logging
import requests
import random
import simplejson as json
import time
import urllib

import httplib2
#import json

import os
import re
import time
import sys

## Uncomment this line for standalone testing
#from flask import Flask

from flask.ext import restful
from flask import redirect, request, current_app, jsonify
import csv, itertools, json
from pprint import pprint

## Comment these lines out for standalone testing
from compass_metrics.api import app
from compass_metrics.utils import flags
from compass_metrics.utils import logsetting
from compass_metrics.utils import setting_wrapper as setting


## Comment out this line for standalone testing
#app = Flask(__name__)

api = restful.Api(app)

webl = httplib2.Http()

## Uncomment this line for standalone testing
#paroff = 3
## Comment out this line for standalone testing
paroff = 6



## Hardcode this line for standalone testing
MONITOR_IP = setting.MONITOR_IP

## Hardcode this line for standalone testing
KAIROS_URL = setting.KAIROS_URL
#KAIROS_URL = "http://10.1.4.71:8080"
#KAIROS_URL = "http://10.145.89.165:8088"

## Hardcode this line for standalone testing
COMPASS_IP = setting.COMPASS_IP
#COMPASS_IP = "10.1.4.70"
#COMPASS_IP = "10.145.89.165"


# Login token - long lived so it's global
token = None


# Support routines

# Builds a unified tree for the enumerated metrics
def apiLogin():
    global token
    if token == None:
        (resp, content) = webl.request("http://"+ COMPASS_IP + "/api/users/token",
                  "POST", body="{\"email\" : \"admin@huawei.com\", \"password\" : \"admin\" }",
                  headers={'Content-Type':'application/json'} )
        #print "Response ="+str(resp)
        #print "Content ="+content
        data = json.loads(content)
        token = data['token']


# Finds the IP address on the management network for a node
def hostMgmtNetIP(net_dict):
    for i, v in enumerate(net_dict):
        if net_dict[v]['is_mgmt']:
            return net_dict[v]['ip']
    return None

# Builds a unified tree for the enumerated metrics
def metricGather(rows, title_root):
    result = []

    for key, group in itertools.groupby(rows, key=lambda r: r[0]):
        group_rows = [row[1:] for row in group]

        s = key
        s = s.replace(" (value)", ".value")
        s = s.replace(" (rx)", ".rx")
        s = s.replace(" (tx)", ".tx")
        s = s.replace(" (read)", ".read")
        s = s.replace(" (write)", ".write")
        s = s.replace(" (free)", ".free")
        s = s.replace(" (used)", ".used")

        if len(group_rows[0]) == 2:
            if title_root != None:
                uid = title_root+'.'+s
            else:
                uid = s
            result.append({u"title": key, u"id": uid, u"nodes": [] })
        elif len(group_rows[0]) < 2:
            continue
        else:
            if title_root != None:
                uid = title_root+'.'+s
            else:
                uid = s
            result.append({u"title": key, u"id": uid, u"nodes": metricGather(group_rows, uid)})

    return result


# Builds a unified tree for the Physical Topology API
def topoGather(rows):
    result = []
    pingip = None
    hostname = None
    for key, group in itertools.groupby(rows, key=lambda r: r[0]):
        group_rows = [row[1:] for row in group]

        if not "@" in key:
            pingip = key
            hostname = key
        else:
            hostinfo = key.split('@', 2)
            pingip = hostinfo[1]
            hostname = hostinfo[0]

        currentState = pingCheck(pingip)

        if len(group_rows[0]) == 0:
            result.append({u"name": hostname, u"ip": pingip, u"state": currentState, u"children": [] })
        else:
            result.append({u"name": hostname, u"ip": pingip, u"state": currentState, u"children": topoGather(group_rows)})

    return result

# Builds a unified tree for the Service Topology API
def serviceGather(rows):
    result = []
    for key, group in itertools.groupby(rows, key=lambda r: r[0]):
        group_rows = [row[1:] for row in group]

        #? Generate Random State
        #currentState = pingCheck(pingip)
        currentState = "ok"

        if len(group_rows[0]) == 0:
            result.append({u"name": key, u"state": currentState, u"children": [] })
        else:
            result.append({u"name": key, u"state": currentState, u"children": serviceGather(group_rows)})

    return result

# Does a quick ping check to see if the host is available on ICMP
def pingCheck(host_or_ip):
# The standalone testing will vary by OS type wrt regex on ping command
    lifeline = re.compile(r"(\d) received")
    #lifeline = re.compile(r"(\d) packets received")
    report = ("critical","warning","ok")

    pingaling = os.popen("ping -q -c2 "+host_or_ip,"r")
    #print host_or_ip," \n",
    sys.stdout.flush()
    while 1:
        line = pingaling.readline()
        if not line: break
        igot = re.findall(lifeline,line)
        if igot:
            return report[int(igot[0])]
    return "unknown"


class HelloInfo(restful.Resource):
    def get(self):
        # return {'info': 'Select host, hostgroup, topology, service from here'}
        url = KAIROS_URL + '/api/v1/tagnames'
        logging.debug('get url %s', url)
        r = requests.get(url)
        logging.debug('%s response: %s', request.path, r)
        return r.json()

api.add_resource(HelloInfo, '/')


class Proxy(restful.Resource):
    def get(self, url):
        # Get URL Parameters for host and metric info
        urlParam = request.url.split('proxy/', 9)
        my_url = urlParam[1]
        # return my_url
        r = requests.get(my_url, stream=True)
        # return r.text
        return json.loads(r.text)
        # return Response(stream_with_context(r.iter_content()), content_type = r.headers['content-type'])

api.add_resource(Proxy, '/proxy/<path:url>', defaults={'url': '/HelloWorld'})


class Hosts(restful.Resource):
    def get(self, clusterid):
        apiLogin()
        clustername = str(clusterid)
        (resp, content) = webl.request("http://"+ COMPASS_IP + "/api/clusters/"+ clustername + "/hosts", "GET", headers={'X-Auth-Token': token, 'Content-Type':'application/json'})
        #print "Response ="+str(resp)
        #print "Content ="+content
        host_dict = json.loads(content)
        s = "{\"hosts\": [\""

        for i, v in enumerate(host_dict):
            s += str(host_dict[i]['hostname']) + "\",\""
	s = s[:-3] # remove unneeded ,\'
        s += "\"]}"

        #return s.json()
        return json.loads(s)

api.add_resource(Hosts, '/clusters/<clusterid>/hosts',
    defaults={'clusterid': '1'} )


class MetricNames(restful.Resource):
    def get(self):
        # we need to tune this to host specific
        req = requests.get(KAIROS_URL +"/api/v1/metricnames")
        names_dict = req.json()
        return names_dict["results"]

api.add_resource(MetricNames, '/metricnames')


class Metrics(restful.Resource):
    def get(self):
        # This is a comprehensive list of metrics not per host due to limitations
        r = requests.get(KAIROS_URL +"/api/v1/metricnames")
        return r.json()

api.add_resource(Metrics, '/metrics')


class MetricTree(restful.Resource):
    def get(self):
        # This is a comprehensive list of metrics not per host due to limitations
        req = requests.get(KAIROS_URL +"/api/v1/metricnames")

        names_dict = req.json()

        s = '.nodes.\n'.join(names_dict["results"])

        s = s.replace(".value", " (value)")
        s = s.replace(".rx", " (rx)")
        s = s.replace(".tx", " (tx)")
        s = s.replace(".read", " (read)")
        s = s.replace(".write", " (write)")
        s = s.replace(".free", " (free)")
        s = s.replace(".used", " (used)")
        #s.replace(".", ".node.")

        rows = list(csv.reader(s.splitlines(), delimiter='.'))
        rws = metricGather(rows, None)
        return rws
        #return json.dumps(rws)
        #return rws.json()

api.add_resource(MetricTree, '/metrictree')


class TsGenerateAlarmData:
    def __init__(self):
	self.params = " "
	self.statusStr = "failure"
	#self.resultStr = " "

	buildStr = '"alarms":['
	buildStr += '{"id":"critical","name":"critical","data":['
        for j in range(1, 30):
            duration = random.randint(0,172800) # number of seconds in 2 days
            starttime = long(time.time() - (j * 86400)) # number of seconds in a day
            endtime = long(starttime + duration/2)
	    buildStr += '{"start":' + str(long(starttime*1000)) + ',"end":' + str(long(endtime*1000)) + '},'

        #remove a comma
	buildStr = buildStr[:-1]
	buildStr += ']},{"id":"minor","name":"minor","data":['
        for j in range(1, 30):
            duration = random.randint(0,172800) # number of seconds in 2 days
            starttime = long(time.time() - (j * 86400)) # number of seconds in a day
            endtime = long(starttime + duration/2)
	    buildStr += '{"start":' + str(long(starttime*1000)) + ',"end":' + str(long(endtime*1000)) + '},'

        #remove a comma
	buildStr = buildStr[:-1]
	buildStr += ']},{"id":"positive","name":"positive","data":['
        for j in range(1, 30):
            duration = random.randint(0,172800) # number of seconds in 2 days
            starttime = long(time.time() - (j * 86400)) # number of seconds in a day
            endtime = long(starttime + duration/2)
	    buildStr += '{"start":' + str(long(starttime*1000)) + ',"end":' + str(long(endtime*1000)) + '},'

        #remove a comma
	buildStr = buildStr[:-1]
	buildStr += ']},{"id":"info","name":"info","data":['
        for j in range(1, 30):
            duration = random.randint(0,172800) # number of seconds in 2 days
            starttime = long(time.time() - (j * 86400)) # number of seconds in a day
            endtime = long(starttime + duration/2)
	    buildStr += '{"start":' + str(long(starttime*1000)) + ',"end":' + str(long(endtime*1000)) + '},'

        #remove a comma
	buildStr = buildStr[:-1]

	self.resultStr = buildStr + ']}]'


class TsPostQuery:
    def __init__(self, queryUrl, queryStr):
        self.params = " "
        self.statusStr = "failure"
        jsqs = json.dumps(queryStr, ensure_ascii=False)
        print "start posting:  " + KAIROS_URL + queryUrl
        r = requests.post(KAIROS_URL + queryUrl, data=jsqs)
        # check the POST status and return success or fail here
        if  r.status_code  == requests.codes.ok:
            self.statusStr = "success"
        print "Post status: " + self.statusStr
        self.resp_dict = r.json()


class TsQueryBuilder:
    def __init__(self, clustername, host_s, metric, multi):
	self.params = " "
	self.statusStr = "failure"
        buildStr = '{ "metrics":['

        repeatStr = json.dumps({
              "tags": {
                  "cluster": [ "CLUSTERID" ],
                  "host": [ "HOSTNAME" ]
              },
              "name": "METRIC",
              "group_by": [
                  {
                      "name":"tag",
                      "tags": ["host"]
                  }
              ],
        "aggregators": [
          {
              "name": "avg",
              "align_sampling": True,
              "sampling": {
                  "value": "1",
                  "unit": "seconds"
              }
            }
          ]
        })

        #finStr = '],"cache_time": 0, "start_relative": { "value": "17", "unit": "minutes" }}'
        finStr = '],"cache_time": 1, "start_relative": { "value": "1", "unit": "months" } }'
        repeatStr = repeatStr.replace("METRIC", metric)

        if multi == True:
            i = len(host_s);
            for hostname in host_s:
                buildStr += repeatStr.replace("HOSTNAME", host_s[i-1]).replace("CLUSTERID", clustername)
                i -= 1
                if i != 0:
                    buildStr += ','
        else:
            buildStr += repeatStr.replace("HOSTNAME", host_s).replace("CLUSTERID", clustername)

        self.params = buildStr + finStr
        print "Query: " + self.params
        r = requests.post(KAIROS_URL +"/api/v1/datapoints/query", data=self.params)

        # check the POST status and return success or fail here
        if  r.status_code  == requests.codes.ok:
	    self.statusStr = "success"
        self.resp_dict = r.json()
        print "Result: " + str(r.json)


class Datapoints(restful.Resource):
    def post(self, clusterid):
        clustername = str(clusterid)
        myReq =  request.get_json(force=True, silent=False, cache=False)
        #print "posting datapoints"
        qb = TsPostQuery("/api/v1/datapoints/query", myReq)
        return qb.resp_dict

api.add_resource(Datapoints, '/clusters/<clusterid>/datapoints',
    defaults={'clusterid': '1'} )


class DatapointTags(restful.Resource):
    def post(self, clusterid):
        clustername = str(clusterid)
        myReq =  request.get_json(force=True, silent=False, cache=False)
        qb = TsPostQuery("/api/v1/datapoints/query/tags", myReq)
        return qb.resp_dict

api.add_resource(DatapointTags, '/clusters/<clusterid>/datapointtags',
    defaults={'clusterid': '1'} )


class HostMetric(restful.Resource):
    def get(self, clusterid, hostname, metricname):
        clustername = str(clusterid)

        # Create and execute the query
        qb = TsQueryBuilder(clustername, hostname, metricname, False)

        # Create JSON Prefix
        valStr = '{"result":[{"metrics":[{"id":"' + hostname + '","data":['

        #  add all time series data
        for key, value in qb.resp_dict["queries"][0]["results"][0]["values"]:
            # round this value down
            digits = str(key)
            key = key - (int(digits[8]) * 10000)
            key = key - (int(digits[9]) * 1000)
            key = key - (int(digits[10]) * 100)
            valStr += '{"time":' + str(key) + ',"value":' + str(value) + '},'

        #remove a comma
	valStr = valStr[:-1]

	#a = TsGenerateAlarmData()
        #add final braces
	valStr += ']}],'
	#valStr += a.resultStr
	valStr += ',"id":"' + hostname + '"}],"status":"' + qb.statusStr + '"}'

        return valStr
        #return json.loads(valStr)


api.add_resource(
    HostMetric,
    '/clusters/<int:clusterid>/hosts/<string:hostname>/metrics/<string:metricname>'
    #,
    #defaults={'clusterid': '1', 'hostname': 'test-controller', 'metricname': 'load.load.shortterm'}
)


class HostGroupMetric(restful.Resource):
    def get(self, clusterid, hostgroup, metricname):
        clusteridname = str(clusterid)

        # need logic to query hostgroup and convert to list
        MyList = ["host1","host2","host3","host4","host5","host6"]

        # Create and execute the query
        qb = TsQueryBuilder(clusteridname, MyList, metricname, True)

        # Create JSON Prefix
        valStr = '{"result":['

        #return qb.resp_dict

        # add all time series data
        i = 0
        for host in MyList:
            valStr += '{"metrics":[{"id":"' + hostgroup + '","data":['
            for skey, svalue in qb.resp_dict["queries"][i]["results"][0]["values"]:
               # round this value down
               digits = str(skey)
               skey = skey - (int(digits[8]) * 10000)
               skey = skey - (int(digits[9]) * 1000)
               skey = skey - (int(digits[10]) * 100)
               valStr += '{"time":' + str(skey) + ',"value":' + str(svalue) + '},'
            #remove a comma
	    valStr = valStr[:-1]

            #add final recordbraces
	    #valStr += ']}],"id":"' + MyList[i] + '"},'

	    a = TsGenerateAlarmData()
            #add final record braces
	    valStr += ']}],'
	    valStr += a.resultStr
	    valStr += ',"id":"' + MyList[i] + '"},'

            i += 1;

        #remove a comma
	valStr = valStr[:-1]

        #add final braces
	valStr += '],"status":"' + qb.statusStr + '"}'

        #return valStr
        return json.loads(valStr)


api.add_resource(
    HostGroupMetric,
    '/clusters/<clusterid>/hostgroups/<hostgroup>/metrics/<metricname>',
    defaults={'clusterid': '1', 'hostname': '', 'metricname': ''}
)


class Alarms(restful.Resource):
    def get(self, clusterid):
        clustername = str(clusterid)
	alarms = TsGenerateAlarmData()
        r = alarms.resultStr
        #return r
        return json.loads("{"+r+"}")

api.add_resource(Alarms, '/clusters/<clusterid>/alarms',
    defaults={'clusterid': '1'} )


class Services(restful.Resource):
    def get(self, clusterid):
        clustername = str(clusterid)
        r = requests.get(KAIROS_URL +"/api/v1/services")
        #return r.json()
        return r

api.add_resource(Services, '/clusters/<clusterid>/services',
    defaults={'clusterid': '1'} )



class Topology(restful.Resource):
    def get(self, clusterid):
        apiLogin()
        clustername = str(clusterid)

        (resp, content) = webl.request("http://"+ COMPASS_IP + "/api/clusters/"+ clustername + "/hosts", "GET", headers={'X-Auth-Token': token, 'Content-Type':'application/json'})
        #print "Response ="+str(resp)
        #print "Content ="+content
        host_dict = json.loads(content)
        s = ""

        for i, v in enumerate(host_dict):
            mgmt_ip = hostMgmtNetIP(host_dict[i]['networks'])
            if mgmt_ip == None:
                mgmt_ip = str(host_dict[i]['hostname'])
            #print "Mngmt net ip: "+mgmt_ip
            s = s + str(host_dict[i]['os_installer']['settings']['cobbler_url'].split('/')[2]) + "," + str(host_dict[i]['switch_ip']) + "," + str(host_dict[i]['hostname']) + "@" + mgmt_ip + "\n"

        rows = list(csv.reader(s.splitlines()))
        print rows
        r = serviceGather(rows)
        #return json.dumps(r)
        return r[0]

api.add_resource(Topology, '/clusters/<clusterid>/topology',
    defaults={'clusterid': '1'} )


class ServiceTopology(restful.Resource):
    def get(self, clusterid):
        apiLogin()
        clusteridname = str(clusterid)
        (resp, content) = webl.request("http://"+ COMPASS_IP + "/api/clusters/"+ clusteridname + "/hosts", "GET", headers={'X-Auth-Token': token, 'Content-Type':'application/json'})
        #print "Response ="+str(resp)
        #print "Content ="+content
        host_dict = json.loads(content)
        s = ""

        for i, v in enumerate(host_dict):
            clustername = host_dict[i]['clustername']
            s = s + "Cluster: " + clustername + "," + str(host_dict[i]['hostname']) + "," + "Disk"+ "\n"
            s = s + "Cluster: " + clustername + "," + str(host_dict[i]['hostname']) + "," + "Load"+ "\n"
            s = s + "Cluster: " + clustername + "," + str(host_dict[i]['hostname']) + "," + "Memory"+ "\n"
            for j, w in enumerate(host_dict[i]['networks']):
                s = s + "Cluster: " + clustername + "," + str(host_dict[i]['hostname']) + "," + "Network" + "," + str(w) + "\n"
            for k, x in enumerate(host_dict[i]['roles']):
                s = s + "Cluster: " + clustername + "," + str(host_dict[i]['hostname']) + "," + "Role" + "," + str(host_dict[i]['roles'][k]['display_name']) + "\n"

        rows = list(csv.reader(s.splitlines()))
        print rows
        r = serviceGather(rows)
        #return json.dumps(r)
        return r[0]


        valStr = '[{"id":"Huawei-Lab-C","name":"Huawei-Lab-C","children":[ {"id":"10.145.81.219","name":"10.145.81.219","state":"warning","resource":"services","type":"service","children":[ {"name":"server-1.huawei.com","id":"host1.huawei.com","state":"running","resource":"hosts","type":"server", "children":[]}, {"name":"server-2.huawei.com","id":"host2.huawei.com","state":"running","resource":"hosts","type":"server", "children":[]}, {"name":"server-3.huawei.com","id":"host3.huawei.com","state":"running","resource":"hosts","type":"server", "children":[]}, {"name":"server-4.huawei.com","id":"host4.huawei.com","state":"running","resource":"hosts","type":"server", "children":[]}, {"name":"server-5.huawei.com","id":"host5.huawei.com","state":"warning","resource":"hosts","type":"server", "children":[]}, {"name":"server-6.huawei.com","id":"host6.huawei.com","state":"running","resource":"hosts","type":"server", "children":[]}, {"name":"server-7.huawei.com","id":"host7.huawei.com","state":"critical","resource":"hosts","type":"server", "children":[]}, {"name":"monit-server-1.huawei.com","id":"10_145_81_205","state":"running","resource":"hosts","type":"server", "children":[]}]}]}]'
        return json.loads(valStr)

api.add_resource(ServiceTopology, '/clusters/<clusterid>/servicetopology',
    defaults={'clusterid': '1'} )


def init():
    pass


#Comment out the 3 init routines for standalone testing
if __name__ == '__main__':
    flags.init()
    logsetting.init()
    init()
    app.run(host='0.0.0.0', debug=True, threaded=True)


"""
# Topo Structure
{"status":"success", "result":[
    {"id":"uc-datacenter","name":"uc-datacenter","children":[
        {"id":"nova-compute","name":"nova-compute","state":"running","resource":"services","type":"service","children":[
            {"id":"compute-server-1.huawei.com","name":"compute-server-1.huawei.com","state":"running","resource":"hosts","type":"server", "children":[
            {"id":"nova-compute","name":"nova-compute","state":"running","resource":"services","type":"service","children":[]},
            {"id":"nova-consoleauth","name":"nova-consoleauth","state":"running","resource":"services","type":"service","children":[]},
            ]},
        {"id":"compute-server-2.huawei.com","name":"compute-server-2.huawei.com","state":"running","resource":"hosts","type":"server", "children":[
            {"id":"nova-novncproxy","name":"nova-novncproxy","state":"running","resource":"services","type":"service","children":[]},
            {"id":"ceilometer-agent-compute","name":"ceilometer-agent-compute","state":"running","resource":"services","type":"service","children":[]},
            {"id":"neutron-openvswitch-agent","name":"nova-openvswitch-agent","state":"running","resource":"services","type":"service","children":[]}
            ]}
        ]}
    ]}
]}

#Query structure
{
  "metrics": [
    {
      "tags": {
        "host": [ "nova-compute_local" ]
      },
      "name": "cpu.0.cpu.idle.value",
      "aggregators": [
        {
          "name": "avg",
          "align_sampling": true,
          "sampling": { "value": "1", "unit": "minutes" }
        }
      ]
    },
    {
      "tags": {
        "host": [ "controller_local" ]
      },
      "name": "cpu.0.cpu.idle.value",
      "aggregators": [
        {
          "name": "avg",
          "align_sampling": true,
          "sampling": { "value": "1", "unit": "minutes" }
        }
      ]
    },
    {
      "tags": {
        "host": [ "nova-compute_local" ]
      },
      "name": "cpu.0.cpu.idle.value",
      "aggregators": [
        {
          "name": "avg",
          "align_sampling": true,
          "sampling": { "value": "1", "unit": "minutes" }
        }
      ]
    },
    {
      "tags": {
        "host": [ "neutron_local" ]
      },
      "name": "cpu.0.cpu.idle.value",
      "aggregators": [
        {
          "name": "avg",
          "align_sampling": true,
          "sampling": { "value": "1", "unit": "minutes" }
        }
      ]
    }
  ],
  "cache_time": 0,
  "start_relative": {
    "value": "1",
    "unit": "hours"
  }
}

# Alarms
{?[?{?[?{.. more json here ...

{"id":"uc-server-1.huawei.com","name":"uc-server-1.huawei.com","resource":"hosts","state":"running","type":"server",  "metrics":[],  "alarms":[
                {"id":"critical","name":"critical","data":[
                                {"start":1406831282409,"end":1406870037149},
                                {"start":1406745382748,"end":1406761927670}
                ]},
                {"id":"minor","name":"minor","data":[
                                {"start":1406873957790,"end":1406886655198},
                                {"start":1406774590378,"end":1406850781190}
                ]},
                {"id":"positive","name":"positive","data":[
                                {"start":1406873957790,"end":1406886655198},
                                {"start":1406774590378,"end":1406850781190}
                ]},
                {"id":"info","name":"info","data":[
                                {"start":1406873957790,"end":1406886655198},
                                {"start":1406774590378,"end":1406850781190}
                ]}
]}
... more json here...?}?]?}?]?}
"""
