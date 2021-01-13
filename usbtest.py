import json
import sys
import time

import serial

jsonBSz = 220  # json buffer size
structSz = 24  # size of structure without payload
pSz = 2  # size position
pSS = 3  # position structure start
posCSmax = pSS + jsonBSz + structSz


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


# {"prog":{"ptrans":30, "pchk":600}}
def buildProgOrder():
    msg = [0] * (posCSmax + 1)
    print("size msg= " + str(len(msg)))
    msg[0] = 0x06
    msg[1] = 0x85
    msg[2] = jsonBSz + structSz  # full size
    url = "scratch"
    for i in range(len(url)):
        msg[pSS + i] = ord(url[i])
    # hostnameTarget = 1
    # msg[pSS + 15:pSS + 16] = hostnameTarget.to_bytes(2, 'little')
    # messageId = 999
    # msg[pSS + 17:pSS + 18] = messageId.to_bytes(2, 'big')
    # msg[pSS + 19] = 0x00
    # xbeeid = 1
    # msg[pSS + 20:pSS + 21] = xbeeid.to_bytes(2, 'big')
    # xbeeNetworkId = 1
    # msg[pSS + 2
    # 2:pSS + 23] = xbeeNetworkId.to_bytes(2, 'big')
    payload = json.dumps({
        "prog": {
            "ptrans": 5,
            "pchk": 600}})
    for i in range(len(payload)):
        msg[pSS + 24 + i] = ord(payload[i])

    return msg


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
            else:
                print("bad message!")

            # print("send= " + str(data[0:data[2] + 4]))
            time.sleep(1)
            alreadySend = True
            if alreadySend == False:
                alreadySend = True
                msg = buildProgOrder()
                cs = computeChecksum(msg)
                msg[msg[pSz] + 3] = cs
                obj = json.loads(extractStruct(msg))
                print(json.dumps(obj, indent=4))
                arduino.write(msg)
                arduino.flush()


# (better to do .read() in the long run for this reason


if __name__ == '__main__':
    main()
