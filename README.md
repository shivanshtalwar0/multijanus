# MultiJanus
Deploy multi port docker instances of janusgateway with ease.

# why?
you can use it to deploy janus instances and use `list` option for gathering  
information related to instances like on which port which service is running.
Please note this script assumes you are running your janus instance with default  
configuration that is default port number for http,websocket and admin api. 

http=>8088  
websocket=>7088  
admin http=>8188  
admin websocket=>7188

# Usage

### Deploy 5 instances with group name janusgateway
    python3 multijanus.py run -n janusserver -i 5

### Delete all instances with specified group name 
    python3 multijanus.py delete -n janusserver

### Get info of all deployed instances with specfied group name
    python3 multijanus.py list -n janusserver          
