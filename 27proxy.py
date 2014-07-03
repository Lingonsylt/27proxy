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
                '<script src="https://ajax.googleapis.com/ajax/libs/jquery/1.9.1/jquery.min.js"></script>',
                '<meta name="viewport" content="width=device-width">\n' +
                '<style type="text/css">\n%s\n</style>\n' % responsive_css +
                '<script src="https://ajax.googleapis.com/ajax/libs/jquery/1.9.1/jquery.min.js"></script>\n' +
                """
                <script type="text/javascript">
                    $(document).ready(function() {
                        $("#map").html('<a href="http://27crags.com%s">Map on original site</a>');
                        $("#map").show();
                        $("#map").attr("id", "no-map");
                    });
                </script>
                """ % self.path)

            content = content.replace(
                '</head>', """
                <script type="text/javascript">
                    var addCell = function(to, from, num, caption, bar) {
                        console.log(from.find("td:nth-child(" + num + ")"));
                        to.append('<span>' + caption + '</span> ' +
                                  from.find("td:nth-child(" + num + ")").text() + '<span>' + bar + '</span>');
                    };

                    $(document).ready(function() {
                        $(".navigation").off();
                        $(".navigation").unbind();
                        window.scrollMonitor = null;

                        $(".topobox").each(function() {
                            var tpbox = $(this);
                            var canvas = tpbox.find("canvas");
                            var canvas_width = canvas.width();

                            tpbox.find(".nbr").each(function() {
                                var jq_elem = $(this);
                                jq_elem.data("orig-left", jq_elem.css('left'));
                                jq_elem.data("orig-top", jq_elem.css('top'));
                            });

                            var updateNBRPositions = function() {
                                var new_canvas_width = canvas.width();
                                var ratio = new_canvas_width / canvas_width;
                                tpbox.find(".nbr").each(function() {
                                    var jq_elem = $(this);
                                    var orig_left = parseInt(jq_elem.data('orig-left'), 10);
                                    jq_elem.css("left", Math.round(orig_left * ratio) + "px");
                                    var orig_top = parseInt(jq_elem.data('orig-top'), 10);
                                    jq_elem.css("top", Math.round(orig_top * ratio) + "px");
                                });
                            };

                            $(window).resize(updateNBRPositions);
                        });

                        $("head").append(" \
                                <style type='text/css'> \
                                @media screen and (max-width: 600px) { \
                                    .topobox { \
                                        width: 100% !important; \
                                    } \
                                    \
                                    .topobox { \
                                        height: auto !important; \
                                    } \
                                    \
                                    .topobox img { \
                                        width: 100% !important; \
                                        height: auto !important; \
                                    } \
                                    \
                                    .topobox canvas { \
                                        width: 100%; \
                                    } \
                                } \
                                </style> \
                                ");

                        $(".topobox").resize();

                        $("table.crags th:last-child").after("<th>+</th>");
                        $("table.crags tr").each(function() {
                            var tr = $(this);
                            var plus = $('<td><a href="#">+</a></td>').insertAfter($(this).find("td:last-child"));

                            var plusHandler = function(evt) {
                                var target  = $(evt.target);
                                if( target.is('a') && target.attr("href") != "#") {
                                    return true;
                                }
                                evt.preventDefault();
                                plus.hide();
                                var new_tr = $('<tr><td class="foldout" colspan="5"></td>').
                                            insertAfter(tr);
                                var new_td = new_tr.find("td");
                                addCell(new_td, tr, 3, '<span class="stars"><div class="star full"></div></span>',
                                                                                                       " &nbsp; ");
                                addCell(new_td, tr, 4, "Routes:", " &nbsp; ");
                                addCell(new_td, tr, 8, "Trad:", " &nbsp; ");
                                addCell(new_td, tr, 10, "Topos:", " &nbsp; ");
                                addCell(new_td, tr, 5, "under 5+:", " &nbsp; ");
                                addCell(new_td, tr, 6, "6a-6c:", " &nbsp; ");
                                addCell(new_td, tr, 6, "6c+-7b:", " &nbsp; ");
                                addCell(new_td, tr, 6, "7b+ over:", "");

                                var minus = $('<td><a href="#">-</a></td>').appendTo(tr);
                                tr.off('click');

                                tr.click(function(evt) {
                                    var target  = $(evt.target);
                                    if( target.is('a') && target.attr("href") != "#") {
                                        return true;
                                    }
                                    evt.preventDefault();
                                    plus.show();
                                    new_tr.remove();
                                    tr.click(plusHandler);
                                    minus.remove();
                                });
                            };

                            tr.click(plusHandler);
                        });
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