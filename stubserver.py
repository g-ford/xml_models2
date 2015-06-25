"""
Copyright 2009 Chris Tarttelin

Redistribution and use in source and binary forms, with or without modification, are
permitted provided that the following conditions are met:

Redistributions of source code must retain the above copyright notice, this list of
conditions and the following disclaimer.

Redistributions in binary form must reproduce the above copyright notice, this list
of conditions and the following disclaimer in the documentation and/or other materials
provided with the distribution.

THIS SOFTWARE IS PROVIDED BY THE FREEBSD PROJECT ``AS IS'' AND ANY EXPRESS OR IMPLIED
WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND
FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE FREEBSD PROJECT OR
CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON
ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING
NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF
ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

The views and conclusions contained in the software and documentation are those of the
authors and should not be interpreted as representing official policies, either expressed
or implied, of the FreeBSD Project.
"""
import BaseHTTPServer, cgi, threading, re, urllib, httplib
import unittest, urllib, urllib2, time
from unittest import TestCase
import sys


class StoppableHTTPServer(BaseHTTPServer.HTTPServer):
    """Python 2.5 HTTPServer does not close down properly when calling server_close.
    The implementation below was based on the comments in the below article:-
    http://stackoverflow.com/questions/268629/how-to-stop-basehttpserver-serveforever-in-a-basehttprequesthandler-subclass
    """
    stopped = False
    allow_reuse_address = True

    def __init__(self, *args, **kw):
        BaseHTTPServer.HTTPServer.__init__(self, *args, **kw)

    def serve_forever(self):
        while not self.stopped:
            self.handle_request()

    def server_close(self):
        BaseHTTPServer.HTTPServer.server_close(self)
        self.stopped = True
        self._create_dummy_request()

    def _create_dummy_request(self):
        f = urllib.urlopen("http://localhost:" + str(self.server_port) + "/__shutdown")
        f.read()
        f.close()


if sys.version_info[0] == 2 and sys.version_info[1] < 6:
    HTTPServer = StoppableHTTPServer
    print "Using stoppable server"
else:
    HTTPServer = BaseHTTPServer.HTTPServer


class StubServer(object):

    _expectations = []

    def __init__(self, port):
        self.port = port

    def run(self):
        server_address = ('localhost', self.port)
        self.httpd = HTTPServer(server_address, StubResponse)
        t = threading.Thread(target=self._run)
        t.start()

    def stop(self):
        self.httpd.server_close()
        self.verify()

    def _run(self, ):
        try:
            self.httpd.serve_forever()
        except:
            pass

    def verify(self):
        failures = []
        for expectation in self._expectations:
            if not expectation.satisfied:
                failures.append(str(expectation))
            self._expectations.remove(expectation)
        if failures:
            raise Exception("Unsatisfied expectations:\n" + "\n".join(failures))

    def expect(self, method="GET", url="^UrlRegExpMatcher$", data=None, data_capture={}, file_content=None):
        expected = Expectation(method, url, data, data_capture)
        self._expectations.append(expected)
        return expected

class Expectation(object):
    def __init__(self, method, url, data, data_capture):
        self.method = method
        self.url = url
        self.data = data
        self.data_capture = data_capture
        self.satisfied = False

    def and_return(self, mime_type="text/html", reply_code=200, content="", file_content=None):
        if file_content:
            f = open(file_content, "r")
            content = f.read()
            f.close()
        self.response = (reply_code, mime_type, content)

    def __str__(self):
        return self.method + ":" + self.url

class StubResponse(BaseHTTPServer.BaseHTTPRequestHandler):

    def __init__(self, request, clientaddress, parent):
        self.expected = StubServer._expectations
        BaseHTTPServer.BaseHTTPRequestHandler.__init__(self, request, clientaddress, parent)

    def _get_data(self):
        if self.headers.has_key("content-length"):
            size_remaining = int(self.headers["content-length"])
            return self._read_chunk(size_remaining)
        elif self.headers.get('Transfer-Encoding', "") == "chunked":
            # Copied from httplib ... should find a way to use httplib instead of copying...
            chunk_left = None
            value = ''
            amt = None
            # XXX This accumulates chunks by repeated string concatenation,
            # which is not efficient as the number or size of chunks gets big.
            while True:
                if chunk_left is None:
                    line = self.rfile.readline()
                    i = line.find(';')
                    if i >= 0:
                        line = line[:i] # strip chunk-extensions
                    chunk_left = int(line, 16)
                    if chunk_left == 0:
                        break
                if amt is None:
                    value += self._read_chunk(chunk_left)
                elif amt < chunk_left:
                    value += self._read_chunk(amt)
                    self.chunk_left = chunk_left - amt
                    return value
                elif amt == chunk_left:
                    value += self._read_chunk(amt)
                    self._read_chunk(2) # toss the CRLF at the end of the chunk
                    self.chunk_left = None
                    return value
                else:
                    value += self._read_chunk(chunk_left)
                    amt -= chunk_left

                # we read the whole chunk, get another
                self._read_chunk(2)     # toss the CRLF at the end of the chunk
                chunk_left = None

            # read and discard trailer up to the CRLF terminator
            ### note: we shouldn't have any trailers!
            while True:
                line = self.rfile.readline()
                if not line:
                    # a vanishingly small number of sites EOF without
                    # sending the trailer
                    break
                if line == '\r\n':
                    break

            # we read everything; close the "file"
            self.rfile.close()

            return value
        else:
            return ""

    def _read_chunk(self, size_remaining):
        max_chunk_size = 10*1024*1024
        L = []
        while size_remaining:
            chunk_size = min(size_remaining, max_chunk_size)
            L.append(self.rfile.read(chunk_size))
            size_remaining -= len(L[-1])
        return ''.join(L)

    def handle_one_request(self):
        """Handle a single HTTP request.

        You normally don't need to override this method; see the class
        __doc__ string for information on how to handle specific HTTP
        commands such as GET and POST.
        """
        self.raw_requestline = self.rfile.readline()
        if not self.raw_requestline:
            self.close_connection = 1
            return
        if not self.parse_request(): # An error code has been sent, just exit
            return
        method = self.command
        if self.path == "/__shutdown":
            self.send_response(200, "Python")
        for exp in self.expected:
            if exp.method == method and re.search(exp.url, self.path) and not exp.satisfied:
                self.send_response(exp.response[0], "Python")
                self.send_header("Content-Type", exp.response[1])
                self.end_headers()
                self.wfile.write(exp.response[2])
                data = self._get_data()
                exp.satisfied = True
                exp.data_capture["body"] = data
                break
        self.wfile.flush()


class WebTest(TestCase):

    def setUp(self):
        self.server = StubServer(8998)
        self.server.run()

    def tearDown(self):
        self.server.stop()
        self.server.verify()

    def _make_request(self, url, method="GET", payload="", headers={}):
        self.opener = urllib2.OpenerDirector()
        self.opener.add_handler(urllib2.HTTPHandler())
        request = urllib2.Request(url, headers=headers, data=payload)
        request.get_method = lambda: method
        response = self.opener.open(request)
        response_code = getattr(response, 'code', -1)
        return (response, response_code)

    def test_get_with_file_call(self):
        f = open('data.txt', 'w')
        f.write("test file")
        f.close()
        self.server.expect(method="GET", url="/address/\d+$").and_return(mime_type="text/xml", file_content="./data.txt")
        response, response_code = self._make_request("http://localhost:8998/address/25", method="GET")
        expected = open("./data.txt", "r").read()
        try:
            self.assertEquals(expected, response.read())
        finally:
            response.close()

    def test_put_with_capture(self):
        capture = {}
        self.server.expect(method="PUT", url="/address/\d+$", data_capture=capture).and_return(reply_code=201)
        f, reply_code = self._make_request("http://localhost:8998/address/45", method="PUT", payload=str({"hello": "world", "hi": "mum"}))
        try:
            self.assertEquals("", f.read())
            captured = eval(capture["body"])
            self.assertEquals("world", captured["hello"])
            self.assertEquals("mum", captured["hi"])
            self.assertEquals(201, reply_code)
        finally:
            f.close()

    def test_post_with_data_and_no_body_response(self):
        self.server.expect(method="POST", url="address/\d+/inhabitant", data='<inhabitant name="Chris"/>').and_return(reply_code=204)
        f, reply_code = self._make_request("http://localhost:8998/address/45/inhabitant", method="POST", payload='<inhabitant name="Chris"/>')
        self.assertEquals(204, reply_code)

    def test_get_with_data(self):
        self.server.expect(method="GET", url="/monitor/server_status$").and_return(content="<html><body>Server is up</body></html>", mime_type="text/html")
        f, reply_code = self._make_request("http://localhost:8998/monitor/server_status", method="GET")
        try:
            self.assertTrue("Server is up" in f.read())
            self.assertEquals(200, reply_code)
        finally:
            f.close()

if __name__=='__main__':
    unittest.main()
