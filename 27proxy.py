from BaseHTTPServer import HTTPServer, BaseHTTPRequestHandler
from SocketServer import ThreadingMixIn
import requests

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        r = requests.get("http://27crags.com%s" % self.path, headers=self.headers.dict)
        self.send_response(200)
        for header, value in r.headers.items():
            if header.lower() in ['date', 'server', 'transfer-encoding', 'content-encoding', 'connection']:
                continue
            self.send_header(header, value)

        if r.headers.get('content-type', "").startswith('text/html'):
            self.send_header("Content-Length", len(r.content))
            self.end_headers()

            with open('responsive.css') as f:
                responsive_css = f.read()
            self.wfile.write(r.content.replace("</head>",
                                               "<meta name=\"viewport\" content=\"width=device-width\">\n" +
                                               "<style type=\"text/css\">\n%s\n</style>\n</head>" % responsive_css))

        else:
            if r.headers.get('content-type', "").startswith('application/json'):
                self.send_header("Content-Length", len(r.content))
            self.end_headers()
            self.wfile.write(r.content)
        return

class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
    """Handle requests in a separate thread."""

if __name__ == '__main__':
    server = ThreadedHTTPServer(('0.0.0.0', 8080), Handler)
    print 'Starting server, use <Ctrl-C> to stop'
    server.serve_forever()