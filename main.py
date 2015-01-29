#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# copyright (c) 2015 luffae@gmail.com
#

from flask import Flask, Response, request, json

app = Flask(__name__)

app.config.from_object('main')
app.config.from_envvar('FLASK_CONFIG')

cacti_list = app.config['CACTI_LIST']


def get_list():
  import MySQLdb

  list = []

  for cacti in cacti_list:
    sql = (
      'SELECT'
      '   CONCAT(' + str(cacti_list.index(cacti)) + ', "_", T1.id)'
      '      AS "chart_id",'
      '   TRIM(SUBSTRING_INDEX(SUBSTRING_INDEX(T2.title, "-", 2), "-", -1))'
      '      AS "chart_type",'
      '   SUBSTRING_INDEX(SUBSTRING_INDEX(T3.description, "-", 1), "-", -1)'
      '      AS "svr_type",'
      '   SUBSTRING_INDEX(SUBSTRING_INDEX(T3.description, "-", 2), "-", -1)'
      '      AS "svr_id",'
      '   T3.description'
      '      AS "svr_name",'
      '   T3.hostname'
      '      AS "svr_ip"'
      ' FROM'
      '   graph_local'
      '      AS T1'
      '   INNER JOIN graph_templates_graph'
      '      AS T2 ON T2.local_graph_id=T1.id'
      '   INNER JOIN host'
      '      AS T3 ON T1.host_id=T3.id')

    db = MySQLdb.connect(**cacti['database'])

    cur = db.cursor(MySQLdb.cursors.DictCursor)
    cur.execute(sql)
    list.extend(cur.fetchall())

    db.close()

  return { 'chart_list': list }


def get_graph(args):
  import time, urllib, re

  get_id = re.search("(\d+)_(\d+)", args['id'])

  if get_id:
    cacti_id = int(get_id.group(1))
    graph_id = int(get_id.group(2))
  else:
    return None

  cacti_list = app.config['CACTI_LIST']

  if (int(cacti_id) > len(cacti_list) - 1):
    return None

  timestamp = int(time.time())

  case = {
    'day'   : { 'o': 3600 * 2,  'p': 3600 * 24       },
    'week'  : { 'o': 3600 * 8,  'p': 3600 * 24 * 7   },
    'month' : { 'o': 3600 * 24, 'p': 3600 * 24 * 31  },
    'year'  : { 'o': 3600 * 24, 'p': 3600 * 24 * 366 }
  }

  if args['type'] not in case:
    return None

  offset = case[args['type']]['o']
  period = case[args['type']]['p']

  time_end = timestamp / offset * offset + offset
  time_start = time_end - period

  data = urllib.urlencode({
    'local_graph_id' : graph_id,
    'graph_start'    : time_start,
    'graph_end'      : time_end
  })
  graph = urllib.urlopen("%s?%s" % (cacti_list[cacti_id]['plot_url'], data))

  return graph.read()


@app.route("/list", methods=["GET"])
def list():
  list = get_list()

  return Response(
         response=json.dumps(list),
         status=200,
         mimetype='application/json')


@app.route("/plot", methods=["GET"])
def plot():
  graph = get_graph(request.args)
  code = 200 if graph else 404

  return Response(
         response=graph,
         status=code,
         mimetype='image/png')


if __name__ == "__main__":
  app.run(host=app.config['SERVER_ADDR'], threaded=True)

