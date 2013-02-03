import codecs
import os
import re
import httplib2
import base64
import mimetypes
from uuid import uuid4
from BeautifulSoup import BeautifulSoup

class DotDict(dict):
    "Enables access to dictionary keys via dot notation"
    def __getattr__(self, attr):
        return self.get(attr, None)
    __setattr__= dict.__setitem__
    __delattr__= dict.__delitem__

def basic_authorize(username, password):
    "Converts user credentials to HTTP Basic Authentication request header."
    return {'Authorization': 'Basic %s' % (base64.b64encode('%s:%s' % (username, password)))}

def post_commentator(func):
    "Provides information about post status; for use as decorator."
    
    def decorated(*args, **kwargs):
        response = func(*args)

        soup = BeautifulSoup(response[1])
        node = args[0]

        status = int(response[0]['status'])
        message = soup.title.text,
        error = None if status in [200, 201] else soup.find('div', id='Message').text

        return DotDict({
            'status': response[0]['status'],
            'node': node,
            'message': soup.title.text,
            'error': error,
            })
    return decorated

def get_content_type(filename):
    "Tries to guess file's mime-type based on extension."
    return mimetypes.guess_type(filename)[0] or 'application/octet-stream'

def encode_multipart(fields, files):
    "Generates multipart form data from supplied fields and files."
    boundary = uuid4().hex
    crlf = '\r\n'
    L = []
    for (name, value) in fields:
        map(lambda x: L.append(x), 
            [   '--%s' % boundary,
                'Content-Disposition: form-data; name="%s"' % name,
                '',
                value,
                ])
    for (name, filename, value) in files:
        map(lambda x: L.append(x), 
            [   '--%s' % boundary,
                'Content-Disposition: form-data; name="%s"; filename="%s"' % (name, filename),
                'Content-Type: %s' % get_content_type(filename),
                '',
                value,
                ])
    L.append('--' + boundary + '--')
    L.append('')
    body = crlf.join(L)
    content_type = 'multipart/form-data; boundary=%s' % boundary
    return content_type, body

@post_commentator
def post_multipart(url, fields=[], files=[], headers={}, credentials=None):
    "Sends a POST containing multipart form data."
    http = httplib2.Http()
    if credentials:
        http.add_credentials(credentials[0], credentials[1])
    content_type, body = encode_multipart(fields, files)
    headers.update({'Content-Type': content_type})
    return http.request(url, 'POST', body, headers=headers)

def get_file_list(path, regex_filter=''):
    "Returns list of all non-directory files under the path, with optional filter."
    file_list = []
    for dirname, dirnames, filenames in os.walk(path):
        for filename in filenames:
           file_list.append(os.path.join(dirname, filename))
    return [f for f in file_list if re.match(regex_filter, f)]

def read_file(file_path, mode='r', encoding=None):
    "Returns content of file at specified path."
    file_obj = codecs.open(file_path, mode, encoding)
    contents = file_obj.read()
    file_obj.close()
    return contents