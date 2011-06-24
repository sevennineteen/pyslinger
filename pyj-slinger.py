import sys
import codecs
import simplejson as json
from helpers import *

#------ CUSTOM PARAMS // pass in via command line---- -------------------------------------
assert len(sys.argv) == 5, "Supply cq_server, username, password, payload_path when calling this script."
cq_server, username, password, payloads_path = sys.argv[1:]

headers = cq_auth_header(username, password) # username, password for CQ user
json_paths = get_file_list(payloads_path) # directory containing JSON payloads
#------------------------------------------------------------------------------------------

def populate_node(path, properties, **kwargs):
    "Organizes properties into form fields and posts the multipart form data."
    
    # properties can be handled as strings by default
    fields = [ (p['name'], p['value']) for p in properties if not p.has_key('type')]
    
    # properties with a type need to be hinted
    hinted = [ hp for hp in properties if hp.has_key('type') ]
    for hp in hinted:
        if hp['value'].__class__.__name__ == 'str':
            fields.append((hp['name'], hp['value'])) # single item
        else:
            map(lambda i: fields.append((hp['name'], i)), hp['value']) # multiple items
        # add the type hint
        fields.append(('%s@TypeHint' % hp['name'], hp['type']))
    
    post_multipart(path, fields, {}, headers, **kwargs)

def main():
    "Iterate through all JSON payloads, passing each node's path and properties."
    for jp in json_paths:
        payload = json.loads(read_file(jp))
    
        # populate the page
        base_path = cq_server + payload['path']
        populate_node(base_path, payload['properties'], label='  Page')
    
        # populate the nodes
        for node in payload['nodes']:
            node_path = '/'.join([base_path, node['path']])
            populate_node(node_path, node['properties'], label='    Node')

if __name__ == "__main__":
    main()