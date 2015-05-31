from BaseHTTPServer import HTTPServer, BaseHTTPRequestHandler
from SocketServer import ThreadingMixIn
import cgi
from pprint import pprint
import urlparse
import requests
import os
import Cookie

PORT = int(os.environ.get("PROXY27_PORT", 8080))
ADDRESS = os.environ.get("PROXY27_ADDRESS", '0.0.0.0')
DEBUG = "PROXY27_DEBUG" in os.environ

class StaticFileServer:
    MIMES = {'css': 'text/css',
             'js': 'text/javascript',
	     'txt': 'text/plain'}

    def __init__(self):
        self.files = {}

    def addFile(self, name):
        with open(name) as f:
            self.files[name] = f.read()

    def fetch(self, url):
        if DEBUG:
            name = url[1:]
            if name in self.files:
                with open(name) as f:
                    return f.read()
            else:
                return False
        else:
            return self.files.get(url[1:], False)

    def getMime(self, url):
        return self.MIMES[url.split(".")[-1]]

sfs = StaticFileServer()
sfs.addFile("responsive.css")
sfs.addFile("early.js")
sfs.addFile("late.js")
sfs.addFile("robots.txt")

class Handler(BaseHTTPRequestHandler):
    def do_POST(self):
        ctype, pdict = cgi.parse_header(self.headers.getheader('content-type'))
        if ctype.startswith('multipart/form-data'):
            self.postdata = cgi.parse_multipart(self.rfile, pdict)
        elif ctype.startswith('application/x-www-form-urlencoded'):
            length = int(self.headers.getheader('content-length'))
            self.postdata = cgi.parse_qs(self.rfile.read(length), keep_blank_values=1)
        else:
            self.postdata = {}
        for key in self.postdata:
            self.postdata[key] = self.postdata[key][0]
        self.handle_request()

    def do_GET(self):
        self.handle_request()

    def handle_request(self):
        parsed_path = urlparse.urlparse(self.path)
        parsed_query = urlparse.parse_qs(parsed_path.query)

        static_data = sfs.fetch(parsed_path.path)
        if static_data:
            self.send_response(200)
            self.send_header("Content-Type", sfs.getMime(parsed_path.path))
            self.end_headers()
            self.wfile.write(static_data)
            return

        protocol = "http"
        if self.path == "/login" or self.headers.get('cookie', '').find('_27crags_session') != -1:
            protocol = "https"

        headers = self.headers.dict.copy()
        host = headers.get('host', '')
        referer = headers.get('referer', '')

        headers['host'] = "27crags.com"
        headers['referer'] = "https://27crags.com/login"
        headers['origin'] = "https://27crags.com"
        if 'accept-encoding' in headers:
            del headers['accept-encoding']
        if 'content-length' in headers:
            del headers['content-length']

        if self.command == "POST":
            if self.path == "/login":
                postkwargs = dict(url="%s://27crags.com%s" % (protocol, self.path), params=self.postdata, headers=headers, allow_redirects=self.path != "/login")
            else:
                postkwargs = dict(url="%s://27crags.com%s" % (protocol, self.path), data=self.postdata, headers=headers, allow_redirects=self.path != "/login")
            pprint(postkwargs)
            r = requests.post(**postkwargs)
        else:
            getkwargs = dict(url="%s://27crags.com%s" % (protocol, self.path), headers=headers)
            pprint(getkwargs)
            r = requests.get(**getkwargs)

        if 'location' in r.headers:
            r.headers['location'] = r.headers['location'].replace("https://27crags.com", '')
            r.headers['location'] = r.headers['location'].replace("http://27crags.com", '')

        self.send_response(r.status_code)
        if self.path == '/logout':
            self.send_header('Set-Cookie', "messages=You%2520were%2520successfully%2520logged%2520out.; path=/")
            self.send_header('Set-Cookie', "auth_token=; path=/; max-age=0; expires=Thu, 01 Jan 1970 00:00:00 -0000")
            self.send_header('Set-Cookie', "auth_id=; path=/; max-age=0; expires=Thu, 01 Jan 1970 00:00:00 -0000")

        for header, value in r.headers.items():
            if header.lower() in ['date', 'server', 'transfer-encoding', 'content-encoding', 'connection', 'content-length']:
                continue
            if header.lower() == 'set-cookie':
                for cookie in Cookie.SimpleCookie(value).values():
                    if 'secure' in cookie:
                        del cookie['secure']
                    self.send_header("Set-Cookie",
                                     cookie.output(header="").strip())
                continue

            self.send_header(header, value)

        print r.status_code
        pprint(r.headers)

        content = r.content
        if r.headers.get('content-type', "").startswith('text/html'):

            if r.status_code == 200 and 'offline' in parsed_query:
                content = r.content.replace("<html ", '<html manifest="%s%scache.manifest"' %
                                                      (parsed_path.path,
                                                       "/" if not parsed_path.path.endswith("/") else ""))
            content = content.replace(
                '<script src="https://ajax.googleapis.com/ajax/libs/jquery/1.9.1/jquery.min.js"></script>',
                '<meta name="viewport" content="width=device-width">\n'
                '<link href="/responsive.css" rel="stylesheet">\n'
                '<script src="https://ajax.googleapis.com/ajax/libs/jquery/1.9.1/jquery.min.js"></script>\n'
                '<script src="/early.js" type="text/javascript"></script>\n')

            content = content.replace('AIzaSyDl0cdA0POqysJWbXxf883-thJXMt_4DcU',
                                      'AIzaSyDDKkln1dq-XOzXzJ4AyZYdyjew3F2dpZw')

            content = content.replace('href="https://27crags.com/login"',
                                      'href="/login"')

            content = content.replace('href="https://localhost:8080/login"',
                                      'href="/login"')

            content = content.replace('action="https://27crags.com/login"',
                                      'action="/login"')

            content = content.replace(
                '</head>',
                '<script src="/late.js" type="text/javascript"></script>\n'
                '</head>')

            self.send_header("Content-Length", len(content))
            self.end_headers()

            self.wfile.write(content)

        else:
            if r.headers.get('content-type', "").startswith('application/json'):
                content = content.replace('https://27crags.com/login', referer)

                content = content.replace('https://27crags.com/', 'http://%s/' % host)
                content = content.replace('http://27crags.com/', 'http://%s/' % host)
                self.send_header("Content-Length", len(content))

                print "response", content

            self.end_headers()

            self.wfile.write(content)
        return

class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
    """Handle requests in a separate thread."""

if __name__ == '__main__':
    server = ThreadedHTTPServer((ADDRESS, PORT), Handler)
    print 'Starting server, use <Ctrl-C> to stop (mode: %s)' % ("DEBUG" if DEBUG else "PROD")
    print "Listening to: %s:%s" % (ADDRESS, PORT)
    server.serve_forever()
