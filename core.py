from easysnmp import Session

# Create an SNMP session to be used for all our requests
session = Session(hostname='10.90.90.90', community='public', version=2)

# все записи lldp
lldp_entries = session.walk('.1.0.8802.1.1.2.1.4.1.1')

# 5 - mac на той стороне
# 7 - portid
# 9 - sysName

sys_descr = session.get('.1.3.6.1.2.1.1.1.0')
sys_name = session.get('.1.3.6.1.2.1.1.5.0')


def mac_bin_to_hex(inc_bin_mac_address):
    octets = [ord(c) for c in inc_bin_mac_address]
    return "{:02X}:{:02X}:{:02X}:{:02X}:{:02X}:{:02X}".format(*octets)


def portnum_convert(hex_string):
    return bytearray.fromhex("31 2f 32 36 00").decode()
