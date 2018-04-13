class Device():
    """
    A 802.11 device.
    """
    def __init__(self):
        self.mac = None
        self.is_ap = None
        self.ssid = None
        self.type = None


class Network():
    """
    An 802.11 network (ESS)
    """
    def __init__(self):
        self.ssid = None
        self.channel = None
        self.frequency = None
        self.auth = None
        self.enc = None
        self.cipher = None


class Connection():
    """
    An authentication/association relationship between two devices
    """
    def __init__(self):
        self.device1 = None
        self.device2 = None
        self.state = None


