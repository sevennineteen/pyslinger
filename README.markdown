# pyj-slinger

## Overview

Pyj-slinger is a simple demonstration of loading content into a Java Content Repository such as [Adobe CQ 5](http://www.day.com/) from a JSON content representation.

A Python script parses the supplied JSON payload(s) and converts the content to a series of multipart form data posts processed by the target system's SlingPostServlet. No special connector code is needed on the target system, as this method takes advantage of Sling's RESTful nature to populate content nodes directly and in place.

More information on the SlingPostServlet is available on the [Apache Sling](http://sling.apache.org/site/manipulating-content-the-slingpostservlet-servletspost.html) site.

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

### Execute Content Load

1. All JSON payloads for migration should be stored under a single directory (nested subfolders are OK).

2. In a terminal, navigate to the directory of `pyj-slinger.py` and issue the following command:

    `python pyj-slinger.py [cq_server] [username] [password] [payloads_path]`

The provided `run_demo.sh` contains a default command appropriate for out-of-the-box CQ instances.

## Caveats

1. While this generalized approach should work on all Sling-fronted repositories, it has only been tested on Adobe CQ 5.4.

2. You may encounter unmet dependencies for Python modules not included in the standard library, such as `simplejson`, `html2text`. Review the import statements at the top of each script and install necessary modules using `easy_install` or `pip`.