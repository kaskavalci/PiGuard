#!/usr/bin/env python

import bluetooth
import datetime
from werkzeug.wrappers import Request, Response
import json

mac_list = []


def check(mac):
    result = bluetooth.lookup_name(mac, timeout=3)
    if result is None:
        return "out"
    else:
        return "in"


@Request.application
def application(request):
    in_out_list = {}
    for mac in mac_list:
        status = check(mac)
        in_out_list[mac] = {"timestamp": str(datetime.datetime.now()), "status": status}
    return Response(json.dumps(in_out_list))

if __name__ == '__main__':
    f = open('mac_list.txt', 'r')
    for line in f:
        mac_list.append(line)

    from werkzeug.serving import run_simple
    run_simple('0', 4000, application)
