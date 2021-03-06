import BaseHTTPServer
import os.path
import json
import cgi
from string import Template

def run(server_class=BaseHTTPServer.HTTPServer,
    handler_class=BaseHTTPServer.BaseHTTPRequestHandler):
  server_address = ('', 3000)
  httpd = server_class(server_address, handler_class)
  httpd.serve_forever()

class TestTemplate(Template):
  delimiter = '%'

staticPrefix = './static/'
templatePrefix = './templates/'

def handle(s, path, prefix, template):
  filepath = os.path.abspath(os.path.join(prefix, path))
  if filepath.startswith(os.path.abspath(prefix)):
    try:
      f = open(filepath,'r')
      s.send_response(200)
      s.end_headers()
      data = f.read()
      if template:
        t = TestTemplate(data)
        data = t.substitute({'host':s.headers['host']})
      s.wfile.write(data)
      return
    except IOError as e:
      print('something went wrong '+str(e))
      pass
  # file is not there (or not within root)
  s.send_response(404)
  s.end_headers()
  s.wfile.write('not found')

def makeHandler(prefix, template):
  def handler(s, path, postvars):
    return handle(s, path, prefix, template)
  return handler

def handleCall(s, path, postvars):
  s.send_response(200)
  s.send_header('Content-type','application/json');
  s.end_headers()
  headers = {}
  for header in s.headers:
    headers[header] = s.headers[header]
  dic = {'path':s.path,'headers':headers,'Result':'Seems to work: '+s.path, 'postvars':postvars}
  data = json.dumps(dic)
  print 'data is '+data
  s.wfile.write(data)

routes = {'/static/':makeHandler(prefix = staticPrefix, template = False),
    '/templates/':makeHandler(prefix = templatePrefix, template = True),
    '/call/':handleCall}

class MyHandler(BaseHTTPServer.BaseHTTPRequestHandler):
  def do_GET(s):
    """Respond to a GET request"""
    for route in routes.keys():
      if s.path.startswith(route):
        return routes[route](s,s.path[len(route):],{})
    s.send_response(200)
    s.send_header('Content-type','text/html')
    s.end_headers()
    s.wfile.write('<html><body><p>maybe you want <a href="/static/docs/api/allclasses-noframe.html">docs</a></body></html>')

  def do_POST(s):
    ctype, pdict = cgi.parse_header(s.headers.getheader('content-type'))
    if ctype == 'multipart/form-data':
        postvars = cgi.parse_multipart(s.rfile, pdict)
    elif ctype == 'application/x-www-form-urlencoded':
        length = int(s.headers.getheader('content-length'))
        postvars = cgi.parse_qs(s.rfile.read(length), keep_blank_values=1)
    else:
        postvars = {}
    for route in routes.keys():
      if s.path.startswith(route):
        return routes[route](s,s.path[len(route):],postvars)
    s.send_response(200)
    s.send_header('Content-type','text/html')
    s.end_headers()
    s.wfile.write('<html><body><p>maybe you want <a href="/static/docs/api/allclasses-noframe.html">docs</a></body></html>')

run(handler_class = MyHandler)
