from BaseHTTPServer import HTTPServer, BaseHTTPRequestHandler
from SocketServer import ThreadingMixIn
import urlparse
import requests
import os

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
    def do_GET(self):
        parsed_path = urlparse.urlparse(self.path)
        parsed_query = urlparse.parse_qs(parsed_path.query)

        static_data = sfs.fetch(parsed_path.path)
        if static_data:
            self.send_response(200)
            self.send_header("Content-Type", sfs.getMime(parsed_path.path))
            self.end_headers()
            self.wfile.write(static_data)
            return

        r = requests.get("http://27crags.com%s" % self.path, headers=self.headers.dict)
        self.send_response(200)

        for header, value in r.headers.items():
            if header.lower() in ['date', 'server', 'transfer-encoding', 'content-encoding', 'connection']:
                continue
            self.send_header(header, value)

        if r.headers.get('content-type', "").startswith('text/html'):
            content = r.content
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

            content = content.replace(
                '</head>',
                '<script src="/late.js" type="text/javascript"></script>\n'
                '</head>')

            self.send_header("Content-Length", len(content))
            self.end_headers()

            self.wfile.write(content)

        else:
            if r.headers.get('content-type', "").startswith('application/json'):
                self.send_header("Content-Length", len(r.content))
            self.end_headers()
            self.wfile.write(r.content)
        return

class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
    """Handle requests in a separate thread."""

if __name__ == '__main__':
    server = ThreadedHTTPServer((ADDRESS, PORT), Handler)
    print 'Starting server, use <Ctrl-C> to stop (mode: %s)' % ("DEBUG" if DEBUG else "PROD")
    print "Listening to: %s:%s" % (ADDRESS, PORT)
    server.serve_forever()
