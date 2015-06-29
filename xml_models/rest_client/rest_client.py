"""
Copyright 2009 Chris Tarttelin and Point2 Technologies

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


__doc__="A REST client, supporting GET, PUT, POST and DELETE"

import urllib2

class Client(object):
    """ 
    A new Client takes a base_url e.g. http://www.mysite.com:8765/rest and 
    optionally a tuple containing username and password for use as basic 
    auth.  
    """
    def __init__(self, base_url, credentials=(None, None)):
        self.base_url = base_url or ""
        self._install_creds(base_url, credentials)
    
    def GET(self, url, headers={}):
        return self._make_request(url, 'GET', None, headers)
        
    def PUT(self, url, payload=None, headers={}):
        return self._make_request(url, 'PUT', payload, headers)
        
    def POST(self, url, payload=None, headers={}):
        return self._make_request(url, 'POST', payload, headers)
        
    def DELETE(self, url, payload=None, headers={}):
            return self._make_request(url, 'DELETE', payload, headers)
        
    def _install_creds(self, base_url, credentials):
        if credentials[0] and credentials[1]:
            user, passwd = credentials
            pwm = urllib2.HTTPPasswordMgrWithDefaultRealm()
            pwm.add_password(None, base_url, user, passwd)
            handler = urllib2.HTTPBasicAuthHandler(pwm)
            handler.set_parent(urllib2.HTTPHandler())
            self.opener = handler.build_opener()
        else:
            self.opener = urllib2.OpenerDirector()
            self.opener.add_handler(urllib2.HTTPHandler())
            self.opener.add_handler(urllib2.HTTPSHandler())
    
    def _make_request(self, url, method, payload, headers):
        request = urllib2.Request(self.base_url + url, headers=headers, data=payload)
        request.get_method = lambda: method
        response = self.opener.open(request)
        response_code = getattr(response, 'code', -1)
        if response_code == -1:
            raise urllib2.HTTPError(url, response_code, "Error accessing external resource", None, None)
        return Response(self.base_url + url, response_code, response.headers, response)
        
class Response(object):
    """Encapsulates the response from a client GET/PUT/POST/DELETE call"""
    
    def __init__(self, url, response_code, headers, content):
        self._url = url
        self._response_code = response_code
        self._headers = dict(headers)
        self._content = content
        
    url = property(fget=lambda : self._url, doc="The url this response was returned from")
    response_code = property(fget=lambda self : self._response_code, doc="The response code returned from the call")
    headers = property(fget=lambda self : self._headers, doc="The headers returned in the response")
    content = property(fget=lambda self : self._content, doc="The response body, as a string, returned from the call")
        
    def expect(self, response_code):
        "If the actual response code does not match the expected response code, raises a HTTPError"
        if self.response_code != response_code:
            raise urllib2.HTTPError(self.url, self.response_code, "Expected response code: %s, but was %s" % (response_code, self.response_code), None, None)
        
    def __getattr__(self, attr_name):
        if self.headers.has_key(attr_name):
            return self.headers[attr_name]
        raise AttributeError
    
    def __str__(self):
        "returns the content of the response as a string"
        return self.content