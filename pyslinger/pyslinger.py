"This script loads supplied JSON payloads into Adobe CQ."

import sys
try: import simplejson as json
except ImportError: import json
from helpers import basic_authorize, post_multipart, get_file_list, read_file, DotDict
from odict import odict

# Initialize constants with sensible defaults
CQ_SERVER = 'http://localhost:4502'
USERNAME = 'admin'
PASSWORD = 'admin'
PAYLOADS_PATH= './payloads'
HEADERS = basic_authorize(USERNAME, PASSWORD) # USERNAME, PASSWORD for CQ user

def verified(receipts):
    "Returns True if no errors found in provided load receipts."
    return DotDict({
        'success': not any([r.error for r in receipts]),
        'url': receipts[0].node,
        'receipts': receipts,
        })

def populate_node(path, properties, **kwargs):
    "Organizes properties into form fields and posts the multipart form data."
    
    # properties can be handled as strings by default
    fields = [(p['name'], p['value']) for p in properties if not p.has_key('type')]
    
    # properties with a type need to be hinted
    hinted = [hp for hp in properties if hp.has_key('type') and hp['type'] != 'nt:file']
    for hp in hinted:
        if hp['value'].__class__.__name__ == 'str':
            fields.append((hp['name'], hp['value'])) # single item
        else:
            map(lambda i: fields.append((hp['name'], i)), hp['value']) # multiple items
        # add the type hint
        fields.append(('%s@TypeHint' % hp['name'], hp['type']))
    
    # properties typed as nt:file should be handled as files
    files = [   (   p['name'], p['value'].split('/')[-1], 
                    read_file(p['value'], 'rb')
                    ) 
                for p in properties 
                if p.has_key('type') and p['type'] == 'nt:file' ]
    if files:
        fields.append(('%s@TypeHint' % p['name'], p['type']))
    
    return post_multipart(path, fields, files, HEADERS, **kwargs)

def slingify(nodes):
    "Returns the node contents as Sling-ready JSON (and any binary file nodes)."
    
    file_nodes = []
    
    def transcribe_node(node):
        "Transcribes nodes into a nested data structure."
        
        # add the node's own properties
        node_name = node['path'].split('/')[-1]
        node_data = odict(  (p['name'], p['value']) for p in node['properties'] 
                            if not p.get('type', None) == 'nt:file' )
        
        # add any binary nodes to file list
        if any(p.get('type', None) == 'nt:file' for p in node['properties']):
            file_nodes.append(node)
        
        # add its child nodes
        for child in get_children(node):
            node_data.update(transcribe_node(child))
        
        return {node_name: node_data}
    
    def get_children(parent):
        "Returns children of the supplied node."
        return [    n for n in nodes 
                    if parent['path'] + '/' in n['path'] 
                    and '/' not in n['path'][len(parent['path']) + 1:]    ]
    
    slingified_json = json.dumps(transcribe_node(sorted(nodes, key=lambda n:n['path'])[0]))
    return slingified_json, file_nodes

def load_item(payload, **kwargs):
    "Loads content item and nodes in a single request, except for binary assets."

    base_path = kwargs.get('base_path', CQ_SERVER + payload['path'])
    
    # assemble content substructure and add to payload properties
    slingified_json, file_nodes = slingify(payload['nodes'])
    
    new_props = (   (':operation', 'import'),
                    (':contentType', 'json'),
                    (':content', slingified_json)
                    )
    map(lambda p: payload['properties'].append({'name': p[0], 'value': p[1]}), new_props)

    receipts = []

    # populate the page
    receipts.append(populate_node(base_path, payload['properties']))
    
    # populate binaries
    for node in file_nodes:
        node_path = '/'.join([base_path, node['path']])
        receipts.append(populate_node(node_path, node['properties']))

    return verified(receipts)

def load_nodes(payload, **kwargs):
    "Loads content item and each node's content as a separate request."

    base_path = kwargs.get('base_path', CQ_SERVER + payload['path'])

    receipts = []
    
    # populate the page
    receipts.append(populate_node(base_path, payload['properties']))
    
    # populate the nodes
    for node in payload['nodes']:
        node_path = '/'.join([base_path, node['path']])
        receipts.append(populate_node(node_path, node['properties']))

    return verified(receipts)

def dump_errors(result):
    "Prints formatted summary of load errors."
    print ' ! Error loading to %s' % result.url
    for r in result.receipts:
        if r.error:
            print '\t[%s] %s' % (r.status, r.node)
            print '\t\t%s' % r.error

def main(mode):
    "Iterates through all JSON payloads, dispatching load according to supplied mode."
    
    modes = {
        'itemwise': load_item,
        'nodewise': load_nodes
    }

    for json_path in JSON_PATHS:
        payload = json.loads(read_file(json_path))
        
        result = modes[mode](payload) # call function corresponding to mode

        if result.success:
            print '   Successfully loaded to %s' % result.url
        else:
            dump_errors(result)

if __name__ == "__main__":
    #------ CUSTOM PARAMS // pass in via command line -----------------------------
    assert len(sys.argv) >= 5, "Supply cq_server, username, password, payloads_path, [mode] when calling this script."
    CQ_SERVER, USERNAME, PASSWORD, PAYLOADS_PATH = sys.argv[1:5]

    try:
        MODE = sys.argv[5]
    except IndexError:
        MODE = 'itemwise'
    assert MODE in ['itemwise', 'nodewise'], "Supported modes are 'itemwise' and 'nodewise'."
    print '...Loading %s...' % MODE

    HEADERS = basic_authorize(USERNAME, PASSWORD) # USERNAME, PASSWORD for CQ user
    JSON_PATHS = get_file_list(PAYLOADS_PATH, '.*\.json') # directory of .json files
    #------------------------------------------------------------------------------

    main(MODE)
