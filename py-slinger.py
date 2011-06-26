import sys
import codecs
import simplejson as json
from helpers import *
from odict import odict

#------ CUSTOM PARAMS // pass in via command line -----------------------------------------
assert len(sys.argv) >= 5, "Supply cq_server, username, password, payload_path, [mode] when calling this script."
cq_server, username, password, payloads_path = sys.argv[1:5]

try:
    mode = sys.argv[5]
except:
    mode = 'itemwise'
assert mode in ['itemwise', 'nodewise'], "Supported modes are 'itemwise' and 'nodewise'."
print '> Loading %s...' % mode

headers = cq_auth_header(username, password) # username, password for CQ user
json_paths = get_file_list(payloads_path, '.*\.json') # directory containing JSON payloads
#------------------------------------------------------------------------------------------

def populate_node(path, properties, **kwargs):
    "Organizes properties into form fields and posts the multipart form data."
    
    # properties can be handled as strings by default
    fields = [ (p['name'], p['value']) for p in properties if not p.has_key('type')]
    
    # properties with a type need to be hinted
    hinted = [ hp for hp in properties if hp.has_key('type') and hp['type'] != 'nt:file']
    for hp in hinted:
        if hp['value'].__class__.__name__ == 'str':
            fields.append((hp['name'], hp['value'])) # single item
        else:
            map(lambda i: fields.append((hp['name'], i)), hp['value']) # multiple items
        # add the type hint
        fields.append(('%s@TypeHint' % hp['name'], hp['type']))
    
    # properties typed as nt:file should be handled as files
    files = [ (p['name'], p['value'].split('/')[-1], read_file(p['value'], 'rb')) for p in properties if p.has_key('type') and p['type'] == 'nt:file']
    if files:
        fields.append(('%s@TypeHint' % p['name'], p['type']))
    
    post_multipart(path, fields, files, headers, **kwargs)

def slingify(nodes):
    "Returns the node contents as Sling-ready JSON (and any binary file nodes)."
    
    file_nodes = []
    
    def transcribe_node(node):
        "Transcribes nodes into a nested data structure."
        
        # add the node's own properties
        node_name = node['path'].split('/')[-1]
        node_data = odict((p['name'], p['value']) for p in node['properties'] if not p.get('type', None) == 'nt:file')
        
        # add any binary nodes to file list
        if any(p.get('type', None) == 'nt:file' for p in node['properties']):
            file_nodes.append(node)
        
        # add its child nodes
        for c in get_children(node):
            node_data.update(transcribe_node(c))
        
        return {node_name: node_data}
    
    def get_children(parent):
        "Returns children of the supplied node."
        return [    n for n in nodes 
                    if parent['path'] + '/' in n['path'] 
                    and '/' not in n['path'][len(parent['path']) + 1:]    ]
    
    slingified_json = json.dumps(transcribe_node(sorted(nodes, key=lambda n:n['path'])[0]))
    return slingified_json, file_nodes

def main(mode):
    "Iterates through all JSON payloads, dispatching load according to supplied mode."
        
    def itemwise():
        "Loads content item and nodes in a single request, except for binary assets."
        
        # assemble content substructure and add to payload properties
        slingified_json, file_nodes = slingify(payload['nodes'])
        
        new_props = (   (':operation', 'import'),
                        (':contentType', 'json'),
                        (':content', slingified_json)
                        )
        map(lambda p: payload['properties'].append({'name': p[0], 'value': p[1]}), new_props)

        # populate the page
        populate_node(base_path, payload['properties'], label='  Content item')
        
        # populate binaries
        for node in file_nodes:
            node_path = '/'.join([base_path, node['path']])
            populate_node(node_path, node['properties'], label='    Binary')
    
    def nodewise():
        "Loads content item and each node's content as a separate request."
        
        # populate the page
        populate_node(base_path, payload['properties'], label='  Content item')
        
        # populate the nodes
        for node in payload['nodes']:
            node_path = '/'.join([base_path, node['path']])
            populate_node(node_path, node['properties'], label='    Node')
    
    for jp in json_paths:
        payload = json.loads(read_file(jp))
        base_path = cq_server + payload['path']
        
        locals()[mode]() # call function corresponding to mode

if __name__ == "__main__":
    main(mode)