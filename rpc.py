import requests
import json
from time import sleep

class RPC(object):
    def __init__(self, username, password, server, port):
        self.url = "http://%s:%s@%s:%s/" % (username, password, server, port)
        self.headers = {'content-type': 'application/json'}
        self.session = requests.Session()

    def get(self, command, params=None):
        if params is None:
            params = []
        payload = {
            "method": command,
            "params": params,
            "jsonrpc": "2.0",
            "id": 0}

        #for i in range(3):
            #try:
        out = self.session.post(self.url, data=json.dumps(payload), headers=self.headers).json()
            #    break
            #except:
            #    print "retrying rpc"
            #    sleep(10)

        try:
            res = json.loads(out)
        except:
            res = {"output": out}
        res['result'] = 'success'
        return res

if __name__ == '__main__':
    from settings import *
    rpc = RPC(RPCUSER, RPCPASS, SERVER, RPCPORT)
    print(rpc.get('getaccountaddress',['test']))
