# Usage: 
# jython pyslinger/pyslinger.py cq_server username password payloads_path [mode]
jython -J-cp ~/Development/jythonlib/jyson-1.0.2.jar pyslinger/pyslinger.py http://localhost:4502 admin admin ./payloads itemwise
jython -J-cp ~/Development/jythonlib/jyson-1.0.2.jar pyslinger/pyslinger.py http://localhost:4502 admin admin ./payloads nodewise