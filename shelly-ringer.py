import xml.etree.ElementTree as ET
import hashlib

import requests

requests.packages.urllib3.disable_warnings()

def create_session(username, password):
    print('Getting session from fritz.box')
    httpResponse = requests.get('https://fritz.box/login_sid.lua?version=2', verify=False)
    contentXml = ET.fromstring(httpResponse.content)
    challenge = contentXml.find('Challenge').text.split('$')
    hash1 = hashlib.pbkdf2_hmac('sha256', password.encode(), bytes.fromhex(challenge[2]), int(challenge[1]))
    hash2 = hashlib.pbkdf2_hmac('sha256', hash1, bytes.fromhex(challenge[4]), int(challenge[3]))
    response = '%s$%s' %(challenge[4], hash2.hex())

    headers = {'Content-Type': 'application/x-www-form-urlencoded'}
    params = {'username': username, 'response': response}

    httpResponse = requests.get('https://fritz.box/login_sid.lua?version=2', verify=False, params=params, headers=headers)
    return ET.fromstring(httpResponse.content).find('SID').text

def logout_session(sid):
    print('Logging out of fritz.box')
    params = {'logout': 1, 'sid': sid}
    requests.get('https://fritz.box/login_sid.lua?version=2', verify=False, params=params)

def ring_fritz_phone(username, password):
    sid = create_session(username, password)
    params = {'idx':'1','sid':sid,'startringtest':'2'}
    print('Ringing fritz.phone')
    requests.get('https://fritz.box/fon_devices/edit_dect_ring_tone.lua', verify=False, params=params)
    logout_session(sid)

if __name__ == '__main__':
    import argparse
    import os
    import sys
    import json

    parser = argparse.ArgumentParser(description='Tool to listen for Shelly Button 1 press and then run an action according to it')
    parser.add_argument('-u', '--unattended', action='store_true', help='Set the unattanded flag. It will exit if there should be user input')
    subparser = parser.add_subparsers(description='Choose if the webserver or pyShelly method of pulling button presses', dest='method')
    subparser.required = True

    parser_pyshelly = subparser.add_parser('pyshelly')
    parser_pyshelly.add_argument('-id', required=True, help='ID of the Shelly Button 1 device. Can be found on the webinterface')

    parser_webserver = subparser.add_parser('webserver')
    parser_webserver.add_argument('-p', '--port', default=8192, help='Port on which the webserver should run on')

    args = parser.parse_args()

    if args.unattended:
        sys.stdout = open(os.devnull, 'w')
        sys.stderr = open(os.devnull, 'w')

    os.chdir(os.path.dirname(sys.argv[0]))

    if not os.path.exists('creds.json'):
        print('Credentials file not found.')
        if args.unattended:
            exit()

        from getpass import getpass
        creds = {}
        creds['username'] = input('Input FritzBox username: ')
        creds['password'] = getpass('Input FritzBox password: ')
        with open('creds.json', 'w') as f:
            json.dump(creds, f)

    with open('creds.json', 'r') as f:
        creds = json.load(f)

    if args.method == 'webserver':
        import http.server

        class NoneHandler(http.server.BaseHTTPRequestHandler):
            def _set_headers(self):
                self.send_response(200)
                self.end_headers()

            def _html(self, message):
                return None

            def do_GET(self):
                sys.stdout = open('log.txt','w')
                self._set_headers()
                ring_fritz_phone(creds['username'], creds['password'])
                sys.stdout.close()

        httpd = http.server.HTTPServer(('', args.port), NoneHandler)
        httpd.serve_forever()

    # not implemented
    elif args.method == 'pyshelly':
        exit('Function not implemented')
        from pyShelly import pyShelly

        def device_added(dev, code):
            print(dev,'',code)

        shelly= pyShelly()
        shelly.cb_device_added.append(device_added)
        shelly.start()
        shelly.discover()

        while True:
            if shelly.devices == []:
                continue
            for device in shelly.devices:
                from pprint import pprint
                pprint(device.__dict__)
                if device.id == args.id:
                    print('FOUND')
                exit()
