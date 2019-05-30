from easysnmp import Session

# Create an SNMP session to be used for all our requests
session = Session(hostname='10.90.90.90', community='public', version=2)

# You may retrieve an individual OID using an SNMP GET
location = session.get('sysLocation.0')

print(location.value)
