import json
import sys
import time

import serial

from pyzabbix import ZabbixMetric, ZabbixSender, ZabbixResponse


jsonBSz = 220  # json buffer size
structSz = 24  # size of structure without payload
pSz = 2  # size position
pSS = 3  # position structure start
posCSmax = pSS + jsonBSz + structSz
# simple parse for arguments
zserver = sys.argv[1]
if zserver.lower().startswith("http"):
    print("Do not prefix the zabbix server name with 'http' or 'https', just specify the hostname or IP")
    sys.exit(1)
hostId = sys.argv[2]
key = "fioxbee"
port = 10051

def computeChecksum(data):
    cs = data[pSz]
    for b in data[pSS:posCSmax]:
        cs ^= b
    return cs


def checkDataIntegrity(data):
    # check preambule must be x06x85
    if len(data) > pSz + 1:
        # print("0x06= " + str(data[0]))
        # print("0x85= " + str(data[1]))
        if data[0] == 0x06 and data[1] == 0x85:
            # verify Checksum
            if len(data) >= posCSmax:
                print(data[pSz])
                cs = data[data[pSz] + 3]
                if cs == computeChecksum(data):
                    return True
    return False


def extractJsonPayload(data):
    obj = json.loads(data)
    print(json.dumps(obj, indent=4))
    print(obj['vbatt'])


def convertBinData(data):
    s = ''
    for b in data:
        if (b == 0): break
        s += chr(b)
    return s


def extractStruct(data):
    endpointUITarget = convertBinData(data[pSS:pSS + 14])
    hostnameTarget = int.from_bytes(data[pSS + 15:pSS + 16], byteorder='little')
    messageId = int.from_bytes(data[pSS + 17:pSS + 18], byteorder='little')
    status = data[pSS + 19]
    xbeeid = int.from_bytes(data[pSS + 20:pSS + 21],
                            byteorder='little')
    xbeeNetworkId = int.from_bytes(data[pSS + 22:pSS + 23],
                                   byteorder='little')
    jpayload = json.loads(convertBinData(data[pSS + 24:pSS + 24 + jsonBSz]))

    return json.dumps({
        "endpointUITarget": endpointUITarget,
        "hostnameTarget": hostnameTarget,
        "messageId": messageId,
        "status": status,
        "xbeeid": xbeeid,
        "xbeeNetworkId": xbeeNetworkId,
        "payload": jpayload,
    })




def main():
    print(sys.version)  # check python version
    print(serial.__version__)  # check pyserial version
    alreadySend = False
    arduino = serial.Serial('/dev/ttyUSB0', 57600, timeout=2)
    time.sleep(1)  # give the connection a second to settle
    while True:
        data = arduino.read(2000)
        if data:
            print(data)  # strip out the new lines for now
            print("size recu= " + str(len(data)))
            if checkDataIntegrity(data):
                print("check ok!")
                obj = json.loads(extractStruct(data))
                print(json.dumps(obj, indent=4))
                print (obj['payload']['vbatt'])
                # Send metrics to zabbix trapper
                xbeeid = obj['payload']['xbeeid']
                freemem = obj['payload']['freemem']
                vbatt = obj['payload']['vbatt']
                packet = [
                    ZabbixMetric(hostId, 'xbeeid', xbeeid)
                    # multiple metrics can be sent in same call for effeciency
                    , ZabbixMetric(hostId, 'freemem', freemem)
                    , ZabbixMetric(hostId, 'vbatt', vbatt)
                ]
                ZabbixResponse = ZabbixSender(zserver, port, use_config=None).send(packet)
                print(ZabbixResponse)
            else:
                print("bad message!")



if __name__ == '__main__':
    main()
