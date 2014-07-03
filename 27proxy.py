from BaseHTTPServer import HTTPServer, BaseHTTPRequestHandler
from SocketServer import ThreadingMixIn
import requests
import os

PORT = int(os.environ.get("PROXY27_PORT", 8080))
ADDRESS = os.environ.get("PROXY27_ADDRESS", '0.0.0.0')
DEBUG = "PROXY27_DEBUG" in os.environ

if not DEBUG:
    with open('responsive.css') as f:
        responsive_css = f.read()

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        global responsive_css
        r = requests.get("http://27crags.com%s" % self.path, headers=self.headers.dict)
        self.send_response(200)
        for header, value in r.headers.items():
            if header.lower() in ['date', 'server', 'transfer-encoding', 'content-encoding', 'connection']:
                continue
            self.send_header(header, value)

        if r.headers.get('content-type', "").startswith('text/html'):
            if DEBUG:
                with open('responsive.css') as f:
                    responsive_css = f.read()
            content = r.content.replace(
                '<script src="https://ajax.googleapis.com/ajax/libs/jquery/1.9.1/jquery.min.js">',
                '<meta name="viewport" content="width=device-width">\n' +
                '<style type="text/css">\n%s\n</style>\n' % responsive_css +
                '<script src="https://ajax.googleapis.com/ajax/libs/jquery/1.9.1/jquery.min.js">')

            content = content.replace(
                '</head>', """
                <script type="text/javascript">
                    $(document).ready(function() {
                        var canvas = $(".topobox canvas");
                        var canvas_width = canvas.width();
                        setTimeout(function() {
                        $("head").append(" \
                            <style type='text/css'> \
                                .pics .topobox { \
                                    width: 100% !important; \
                                } \
                                \
                                .pics .topobox { \
                                    height: auto !important; \
                                } \
                                \
                                .topobox img { \
                                    width: 100%; \
                                    height: auto; \
                                } \
                                \
                                .topobox canvas { \
                                    width: 100%; \
                                } \
                            </style> \
                        ");

                        var new_canvas_width = canvas.width();
                        var ratio = new_canvas_width / canvas_width;
                        $(".topobox .nbr").each(function() {
                            var jq_elem = $(this);
                            var left = parseInt(jq_elem.css('left'), 10);
                            jq_elem.css("left", Math.round(left * ratio) + "px");
                            var top = parseInt(jq_elem.css('top'), 10);
                            jq_elem.css("top", Math.round(top * ratio) + "px");
                        });
                        }, 0);
                    });
                </script>
                </head>""")

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