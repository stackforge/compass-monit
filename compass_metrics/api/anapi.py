#!/usr/bin/env python

from flask import Flask
from flask.ext import restful
from flask.ext.restful import reqparse
from flask.ext.jsonpify import jsonify
#from flask import request
from flask import redirect, request, current_app
import urllib
import json 
import requests 
import random 
import time 


app = Flask(__name__)


api = restful.Api(app)

#class MyEncoder1(json.JSONEncoder):
#    def default(self, obj):


class HelloWorld(restful.Resource):
    def get(self):
        return {'warning': 'Please use /monit/api'}

api.add_resource(HelloWorld, '/', '/monit')

class HelloInfo(restful.Resource):
    def get(self):
        #return {'info': 'Select host, hostgroup, topology, service from here'}
        r = requests.get(ROOT_URL+"/api/v1/tagnames")
        return r.json()

api.add_resource(HelloInfo, '/monit/api')

class Proxy(restful.Resource):
    def get(self, url):
        # Get URL Parameters for host and metric info
        urlParam = request.url.split('proxy/', 9);
        my_url = urlParam[1]
        #return my_url
        r = requests.get(my_url, stream = True)
        #return r.text
        return json.loads(r.text)
        #return Response(stream_with_context(r.iter_content()), content_type = r.headers['content-type'])

api.add_resource(Proxy, '/monit/api/proxy/<path:url>', defaults={'url': '/HelloWorld'})

class InvalidUrl(restful.Resource):
    def get(self):
        return {'warning': 'Please form the URL'}

api.add_resource(InvalidUrl, '/monit')

class Hosts(restful.Resource):
    def get(self):
        return {'hosts': '[\'host1\',\'host2\',\'host3\',\'host4\',\'host5\',\'host6\']'}
        r = requests.get(ROOT_URL +"/api/v1/tagvalues")
	# weed out just the hosts if possible
        return r.json()

api.add_resource(Hosts, '/monit/api/hosts')

class Metrics(restful.Resource):
    def get(self):
        # This is a comprehensive list of metrics not per host due to limitations
        r = requests.get(ROOT_URL +"/api/v1/metricnames")
        return r.json()

api.add_resource(Metrics, '/monit/api/metrics')

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


class TsQueryBuilder:
    def __init__(self, host_s, metric):
	self.params = " "
	self.statusStr = "failure"
        buildStr = '{ "metrics":['

        repeatStr = '{"tags":{ "host":["HOSTNAME"]},"name":"METRIC","group_by":[{"name":"tag", "tags":["host"]}],"aggregators":[{"name":"sum", "align_sampling": false, "sampling":{ "value": "2", "unit": "minutes"}}]}'
        finStr = '],"start_relative": { "value": "17", "unit": "minutes" }}' 
        repeatStr = repeatStr.replace("METRIC", metric)

        i = len(host_s);
        for hostname in host_s:
            buildStr += repeatStr.replace("HOSTNAME", host_s[i-1])
            i -= 1
            if i != 0:
                buildStr += ','
        self.params = buildStr + finStr
        #print "Query: " + self.params
        r = requests.post(ROOT_URL +"/api/v1/datapoints/query", data=self.params)

        # check the POST status and return success or fail here
        if  r.status_code  == requests.codes.ok:
	    self.statusStr = "success"
        self.resp_dict = r.json()

class HostMetric(restful.Resource):
    def get(self, hostname, metricname):
        # Get URL Parameters for host and metric info
        urlParam = request.url.split('/', 9);
        MyList = [urlParam[6]]

        # Create and execute the query
        qb = TsQueryBuilder(MyList, urlParam[8])

        # Create JSON Prefix
        valStr = '{"result":[{"metrics":[{"id":"' + urlParam[8] + '","data":['

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

	a = TsGenerateAlarmData()
        #add final braces
	valStr += ']}],'
	valStr += a.resultStr
	valStr += ',"id":"' + urlParam[6] + '"}],"status":"' + qb.statusStr + '"}'

        #return valStr
        return json.loads(valStr)

api.add_resource(
    HostMetric, 
    '/monit/api/host/<hostname>/metric/<metricname>', 
    defaults={'hostname': '', 'metricname': ''}
)

class HostGroupMetric(restful.Resource):
    def get(self, hostgroup, metricname):
        # Get URL Parameters for host and metric info
        urlParam = request.url.split('/', 9);
        hostgroup = urlParam[6]

        # need logic to query hostgroup and convert to list
        MyList = ["host1","host2","host3","host4","host5","host6"]

        # Create and execute the query
        qb = TsQueryBuilder(MyList, urlParam[8])

        # Create JSON Prefix
        valStr = '{"result":['

        #return qb.resp_dict

        # add all time series data
        i = 0
        for host in MyList:
            valStr += '{"metrics":[{"id":"' + urlParam[8] + '","data":['
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
    '/monit/api/hostgroup/<hostgroup>/metric/<metricname>', 
    defaults={'hostgroup': '', 'metricname': ''}
)


class RsHostMetric(restful.Resource):
    def get(self, hostname, metricname):
        # Get URL Parameters for host and metric info
        urlParam = request.url.split('/', 9);
        MyList = [urlParam[6]]

        # Create and execute the query
        qb = TsQueryBuilder(MyList, urlParam[8])

        # Create JSON Prefix
        valStr = '{"series":[{"metrics":[{"id":"' + urlParam[8] + '","data":['

        # add all time series data
        for key, value in qb.resp_dict["queries"][0]["results"][0]["values"]:
            # round this value down
            digits = str(key)
            key = key - (int(digits[8]) * 10000)
            key = key - (int(digits[9]) * 1000)
            key = key - (int(digits[10]) * 100)
            valStr += '{"time":' + str(key) + ',"value":' + str(value) + '},'

        #remove a comma
	valStr = valStr[:-1]

        #add final braces
	valStr += ']}],"id":"' + urlParam[6] + '"}],"status":"' + qb.statusStr + '"}'

        return json.loads(valStr)

api.add_resource(
    RsHostMetric, 
    '/monit/api/rshost/<hostname>/metric/<metricname>', 
    defaults={'hostname': '', 'metricname': ''}
)

class RsHostGroupMetric(restful.Resource):
    def get(self, hostgroup, metricname):
        # Get URL Parameters for host and metric info
        urlParam = request.url.split('/', 9) #;
        urlCruft = urlParam[8].split('?', 2) #;
        hostgroup = urlParam[6]
        themetric = urlCruft[0]

        print themetric

        # need logic to query hostgroup and convert to list
        MyList = ["host1","host2","host3","host4","host5","host6"]

        # Create and execute the query
        qb = TsQueryBuilder(MyList, themetric)

        # Create JSON Prefix
        valStr = '['

        #return qb.resp_dict

        # add all time series data
        i = 0
        for host in MyList:
            valStr += '{"name":"' + MyList[i] + ": " + themetric + '","data":['
            for skey, svalue in qb.resp_dict["queries"][i]["results"][0]["values"]:
               # round this value down
               digits = str(skey)
               skey = skey - (int(digits[8]) * 10000)
               skey = skey - (int(digits[9]) * 1000)
               skey = skey - (int(digits[10]) * 100)
               valStr += '{"x":' + str(skey) + ',"y":' + str(svalue) + '},'

            #remove a comma
	    valStr = valStr[:-1]

            #add final recordbraces
	    valStr += ']},'

            i += 1;

        #remove a comma
	valStr = valStr[:-1]

        #add final braces
	valStr += ']'

        callback = request.args.get('callback', False)
        if callback:
            content = str(callback) + '(' + valStr + ')'
            return current_app.response_class(content, mimetype='application/json')

        #return valStr
        return json.loads(valStr)

api.add_resource(
    RsHostGroupMetric, 
    '/monit/api/rshostgroup/<hostgroup>/metric/<metricname>', 
    defaults={'hostgroup': '', 'metricname': ''}
)

class Alarms(restful.Resource):
    def get(self):
	alarms = TsGenerateAlarmData()
        r = alarms.resultStr
        #return r
        return json.loads("{"+r+"}")

api.add_resource(Alarms, '/monit/api/alarms')

class Services(restful.Resource):
    def get(self):
        r = requests.get(ROOT_URL +"/api/v1/services")
        return r.json()

api.add_resource(Services, '/monit/api/services')

class Topology(restful.Resource):
    def get(self):
        #r = requests.get(ROOT_URL +"/api/v1/topology")
        #return r.json()
        valAStr = '{"status":"success", "result":[ {"id":"uc-datacenter","name":"uc-datacenter","children":[ {"id":"nova-compute","name":"nova-compute","state":"running","resource":"services","type":"service","children":[ {"id":"compute-server-1.huawei.com","name":"compute-server-1.huawei.com","state":"running","resource":"hosts","type":"server", "children":[ {"id":"nova-compute","name":"nova-compute","state":"running","resource":"services","type":"service","children":[]}, {"id":"nova-consoleauth","name":"nova-consoleauth","state":"running","resource":"services","type":"service","children":[]} ]}, {"id":"compute-server-2.huawei.com","name":"compute-server-2.huawei.com","state":"running","resource":"hosts","type":"server", "children":[ {"id":"nova-novncproxy","name":"nova-novncproxy","state":"running","resource":"services","type":"service","children":[]}, {"id":"ceilometer-agent-compute","name":"ceilometer-agent-compute","state":"running","resource":"services","type":"service","children":[]}, {"id":"neutron-openvswitch-agent","name":"nova-openvswitch-agent","state":"running","resource":"services","type":"service","children":[]} ]} ]} ]} ]}'

        valStr = '{"status":"success", "result":[{"id":"Huawei-Lab-C","name":"Huawei-Lab-C","children":[ {"id":"10.145.81.219","name":"10.145.81.219","state":"warning","resource":"services","type":"service","children":[ {"name":"server-1.huawei.com","id":"host1.huawei.com","state":"running","resource":"hosts","type":"server", "children":[]}, {"name":"server-2.huawei.com","id":"host2.huawei.com","state":"running","resource":"hosts","type":"server", "children":[]}, {"name":"server-3.huawei.com","id":"host3.huawei.com","state":"running","resource":"hosts","type":"server", "children":[]}, {"name":"server-4.huawei.com","id":"host4.huawei.com","state":"running","resource":"hosts","type":"server", "children":[]}, {"name":"server-5.huawei.com","id":"host5.huawei.com","state":"warning","resource":"hosts","type":"server", "children":[]}, {"name":"server-6.huawei.com","id":"host6.huawei.com","state":"running","resource":"hosts","type":"server", "children":[]}, {"name":"server-7.huawei.com","id":"host7.huawei.com","state":"critical","resource":"hosts","type":"server", "children":[]}, {"name":"monit-server-1.huawei.com","id":"10_145_81_205","state":"running","resource":"hosts","type":"server", "children":[]}]}]}]}'
        return json.loads(valStr)

        #return valStr

api.add_resource(Topology, '/monit/api/topologies/1')

if __name__ == '__main__':
    global ROOT_URL
    ROOT_URL = "http://10.145.81.205:8080"
    app.run(host='0.0.0.0', debug=True, threaded=True)
    #app.run(debug=True)



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
