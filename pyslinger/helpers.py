import codecs
import os
import re
import httplib2
import base64
import mimetypes
from uuid import uuid4
from html2text import html2text

def cq_auth_header(username, password):
    "Converts user credentials to CQ-required request header."
    return {'Authorization': 'Basic %s' % (base64.b64encode('%s:%s' % (username, password)))}

def post_commentator(func):
    "Provides information about post status; for use as decorator."
    statuses = { '200': 'updated', '201': 'created' }
    
    def decorated(*args, **kwargs):
        response = func(*args)
        try:
            print '%s %s: %s' % (kwargs.get('label', 'Node'), statuses[response[0]['status']], args[0])
        except:
            try:
                print html2text(response[1]).replace('\n\n', '\n')
            except:
                print response[1]
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
    try:
        file_obj = codecs.open(file_path, mode, encoding)
        contents = file_obj.read()
        file_obj.close()
        return contents
    except:
        print 'Could not ingest file at path: %s' % file_path