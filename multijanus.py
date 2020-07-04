import socket
from contextlib import closing
import sys
import argparse
import subprocess
from subprocess import PIPE
import os

port_mapping = {
    7088: 'http_admin',
    8188: 'websocket',
    7188: 'websocket_admin',
    8088: 'http',
    80:'http_server'
}

run_template = '''docker run --name "{name}_{index}" -it -d -p {http_admin}:7088 -p {websocket_admin}:7188/tcp -p {websocket_admin}:7188/udp -p {http}:8088 -p {websocket}:8188/tcp -p {websocket}:8188/udp shivanshtalwar0/janusgateway'''

delete_template = '''docker rm $(docker ps -aq --filter name={name}_*)'''

start_janus = "docker exec {name}_{index} /opt/janus/bin/janus -b --log-file januslogfile -a SecureIt"


def start_janus_server(Name, index):
    return subprocess.Popen(start_janus.format(name=Name, index=index + 1), shell=True, stdout=PIPE,
                            stderr=PIPE).communicate()


def get_port():
    with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as s:
        s.bind(('', 0))
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        return s.getsockname()[1]


def delete_containers(Name):
    return subprocess.Popen(delete_template.format(name=Name), shell=True, stdout=PIPE, stderr=PIPE).communicate()


def stop_containers(Name):
    return subprocess.Popen("docker stop $(docker ps -aq --filter name={name}_*)".format(name=Name), shell=True,
                            stdout=PIPE, stderr=PIPE).communicate()


def start_containers(Name, instances):
    for i in range(instances):
        http = get_port()
        websocket = get_port()
        http_admin = get_port()
        websocket_admin = get_port()
        output, error = subprocess.Popen(run_template.format(name=Name,
                                                             index=i + 1,
                                                             http=http,
                                                             websocket=websocket,
                                                             http_admin=http_admin,
                                                             websocket_admin=websocket_admin
                                                             ), shell=True,
                                         stdout=PIPE, stderr=PIPE).communicate()
        # print(output.decode())
        if error.startswith(b'docker: Error response from daemon: Conflict. The container name'):
            print('instance already running doing nothing.')
        else:
            joutput, jerror = start_janus_server(name, i)
            print(joutput)
            print('''
                        http_api\t=>\thttp://127.0.0.1:{http}/janus\n
                        websocket_api\t=>\tws://127.0.0.1:{websocket}\n
                        http_admin_api\t=>\thttp://127.0.0.1:{http_admin}/admin\n
                        websocket_admin_api\t=>\tws://127.0.0.1:{websocket_admin}\n                        
                        '''.format(http=http, http_admin=http_admin, websocket=websocket,
                                   websocket_admin=websocket_admin))


parser = argparse.ArgumentParser(description='deploy multiple janus docker instances')
parser.add_argument('action', nargs=1,
                    help='run => To spawn multiple instances\n , delete => To delete all spawned instances with '
                         'specified group name, list => get info of all active instances')
parser.add_argument('--name', '-n', nargs=1,
                    required=True,
                    help='name of janus instance group')
parser.add_argument('--instances', '-i', nargs=1, type=int,
                    help='number of janus instance to be created')

args = parser.parse_args()
action = args.action[0]
name = args.name[0]

if (action == 'run'):
    if (args.instances == None):
        print('-i or --instances required!')
    else:
        start_containers(name, args.instances[0])


elif (action == 'delete'):
    output, error = delete_containers(name)
    if error.startswith(b'"docker rm" requires at least 1 argument.'):
        print('No instance available to delete with name ' + name)
    if error.startswith(b'Error response from daemon: You cannot remove a running container '):
        print('container running stopping and then closing')
        output, error = stop_containers(name)
        print('stopped instance with id ' + output.decode())
        output, error = delete_containers(name)
        print('again deleting ' + output.decode())
elif (action == 'list'):
    output, error = subprocess.Popen(
        'docker ps --format "{{{{.Names}}}}: {{{{.Ports}}}}" --filter name={name}_*'.format(name=name), shell=True,
        stdout=PIPE, stderr=PIPE).communicate()
    result = []
    data = [x.split(' ') for x in output.decode().split('\n')][:-1]
    for a in data:
        urls = {}
        for b in a[2:]:
            ports = b.split('->')
            iport = int(ports[-1].split('/')[0])
            target_url = ports[0]
            endpoint=''
            if port_mapping[iport].startswith('http') and port_mapping[iport].endswith('admin'):
                endpoint='/admin'
            if port_mapping[iport]=='http':
                endpoint='/janus'  
            urls.update(
                {port_mapping[iport]: ('http://' if port_mapping[iport].startswith('http') else 'wss://') + target_url+endpoint})
        result.append({'name': a[0], 'urls': urls})
    print(result)



else:
    print('invalid action type')
