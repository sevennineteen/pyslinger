# pyslinger

## Overview

Pyslinger is a simple module for loading content into a Java Content Repository such as [Adobe CQ5](http://www.day.com/) from a JSON content representation.

The module parses the supplied JSON payload(s) and converts the content to a series of multipart form data posts processed by the target system's SlingPostServlet. No special connector code is needed on the target system, as this method takes advantage of Sling's RESTful nature to populate content nodes directly and in place.

More information on the SlingPostServlet is available on the [Apache Sling](http://sling.apache.org/site/manipulating-content-the-slingpostservlet-servletspost.html) site.

## Installation

    pip install -e git+https://github.com/sevennineteen/pyslinger.git#egg=Pyslinger

## Usage

### Construct JSON Payloads

Each JSON payload should be structured in the following format:

    { "path": "*/absolute/page/path*",
      "properties": [
        { "name": "*property_name*",
          "value": "*property_value*" }],
    
      "nodes": [
        { "path": "*node/path/relative/to/page*",
          "properties": [
            { "name": "*property_name*",
              "value": "*property_value*"},
            { "name": "*property_name*",
              "type": "*property_type*",
              "value": ["*value1*", "*value2*", "*value3*"] }]},
    
        { "path": "*node/path/relative/to/page*",
          "properties": [
            { "name": "*property_name*",
              "value": "*property_value*"}]}
      ]
    }

By default, properties are assumed to be of type `String` and therefore the `type` is omitted. For non-scalar values such as arrays (e.g., multiple tags in CQ), the `type` must be explicitly declared in the JSON payload.

See the supplied `page_example.json` file for a real-world representation of a CQ Geometrixx page.

> Loading binary files (e.g., images) is also supported. The JSON payload follows a similar format, but includes a renditions node which includes a path to the local file. The supplied `asset_example.json` payload is used to load `austin_motel.jpg`.

### Content Load Execution

Pyslinger may be used as a standalone script (loading JSON payloads within a directory) or integrated into an application as a Python module.

#### Standalone Script Execution

1. All JSON payloads for migration should be stored under a single directory (nested subfolders are OK).

2. In a terminal, navigate to the directory of `pyslinger.py` and issue the following command:

    `python pyslinger/pyslinger.py cq_server username password payloads_path [mode]`

> Supported modes are `itemwise` and `nodewise`. 

> In *itemwise* mode, a single POST request is used to load the content item, followed by separate requests for associated binary files (if any).

> In *nodewise* mode, a separate POST request is made for each node. This may be useful for debugging or making very precise updates.

The provided `run_demo.sh` contains default commands appropriate for out-of-the-box CQ instances. This executes the script twice, loading content *itemwise* and *nodewise*, respectively.

#### Python Module API

In the context of a larger migration project, it may be beneficial to incorporate Pyslinger as a module, accessing its load functions directly. In this paradigm, the generated JSON payloads may be loaded directly without even writing them to disk.

For example, using a templating language like [Jinja2](http://jinja.pocoo.org/docs/) to generate the payload, you might implement this process as follows:

    from jinja2 import Environment, PackageLoader
    from pyslinger import pyslinger

    # Set destination server/credentials if not defaults
    pyslinger.CQ_SERVER = 'http://cqdev:4502'
    pyslinger.USERNAME = 'megaman'
    pyslinger.PASSWORD = 'P@55w0rd'

    # Set the Jinja2 template
    env = Environment(loader=PackageLoader('app', 'templates'))
    template = env.get_template('page_template.json')

    # Set values to be passed to the template
    mypage = {
        'title': 'Welcome to Pyslinger',
        'description': 'A page loaded into CQ using Pyslinger'
        }

    # Render the payload
    payload = template.render(page=mypage)

    # Load using Pyslinger
    result = pyslinger.load_item(json.loads(payload))
    if result.success:
        print 'Loaded to %s' % result.item
    else:
        pyslinger.dump_errors(result)

## Caveats

1. While this generalized approach should work on all Sling-fronted repositories, it has only been tested on Adobe CQ 5.4 and 5.5.