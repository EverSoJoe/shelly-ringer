import requests

def ring_fritz_phone():
    print('testing')

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='Tool to listen for Shelly Button 1 press and then run an action according to it')
    subparser = parser.add_subparsers(description='Choose if the webserver or pyShelly method of pulling button presses', dest='method')
    subparser.required = True

    parser_pyshelly = subparser.add_parser('pyshelly')
    parser_pyshelly.add_argument('-id', required=True, help='ID of the Shelly Button 1 device. Can be found on the webinterface')

    parser_webserver = subparser.add_parser('webserver')
    parser_webserver.add_argument('-p', '--port', default=8192, help='Port on which the webserver should run on')

    args = parser.parse_args()

    if args.method == 'webserver':
        import http.server

    class NoneHandler(http.server.BaseHTTPRequestHandler):
        def _set_headers(self):
            self.send_response(200)
            self.end_headers()

        def _html(self, message):
            return None

        def do_GET(self):
            self._set_headers()
            ring_fritz_phone()
    
    httpd = http.server.HTTPServer(('', args.port), NoneHandler)
    httpd.serve_forever()

    # not completely implemented
    if args.method == 'pyshelly':
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