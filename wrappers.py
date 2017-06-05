import jinja2
import pexpect
import requests
import munch
from lxml import etree
import csv
from collections import defaultdict



def return_jinja_rendered_output(jinja_template_file, in_dict, path="./"):

    template_loader = jinja2.FileSystemLoader(searchpath=path)

    template_env = jinja2.Environment(loader=template_loader)

    try:
        template = template_env.get_template(jinja_template_file)
    except jinja2.exceptions.TemplateNotFound:
        return False, None

    return True, template.render(in_dict)


def run_snmp_walk(mgmt_ip, community, oid):
    snmp_output = pexpect.run('snmpbulkwalk -Os -c {0} -v 2c {1} {2}'.format(community,
                                                                             mgmt_ip,
                                                                             oid))

    # Run command using pexpect and return the output from the command
    return snmp_output.decode("utf-8")


def get_peering_db_six_pfx_len(ix_id):
    try:
        data = requests.get('https://www.peeringdb.com/api/ixpfx?ixlan_id={0}'.format(ix_id))
        return data.json()['data']
    except Exception:
        return {}


def get_seattle_six_peering(ix_id):
    try:
        data = requests.get('https://www.peeringdb.com/api/netixlan?ix_id={0}&depth=2'.format(ix_id))
        return data.json()['data']
    except Exception:
        return {}


def get_ix_lan_iface(ix_id):
    prefix_len_stuff = get_peering_db_six_pfx_len(ix_id)
    for item in prefix_len_stuff:
        if item['protocol'] == 'IPv4':
            ipv4_cidr = item['prefix'].split('/')[1]
        else:
            ipv6_cidr = item['prefix'].split('/')[1]


    peers = get_seattle_six_peering(ix_id)

    for peer in peers:
        if peer['asn'] == '32934':
            ipv4_addr = str(peer['ipaddr4'])
            ipv6_addr = str(peer['ipaddr6'])

    return ipv4_addr, ipv4_cidr, ipv6_addr, ipv6_addr




def generate_munch_device(name, vendor, pid, arch_type, oper_state):
    return munch.Munch({
        'name': name,
        'vendor': vendor,
        'product': pid,
        'arch_type': arch_type,
        'oper_state': oper_state
        }
    )


def create_xml_devices(file_name):
    devices = etree.Element("Devices")

    with open(file_name) as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            new_device = etree.SubElement(devices, "Device")
            create_xml_device(new_device,
                row['name'], row['vendor'],
                row['pid'], row['ix'], row['state'])

    return etree.tostring(devices, pretty_print=True)


def create_xml_device(device, name: str, vendor: str, pid: str, ix: str, state: str):

    device.set("name", name)
    device.set("vendor", vendor)
    device.set("pid", pid)
    device.set("ix", ix)
    device.set("state", state)

    get_bgp_element(device)
    get_physical_element(device)

    return device


def generated_device_file():
    with open('generated_devices.xml', 'wb') as f:
        f.write(create_xml_devices(('devices.csv')))


def get_xml_root(xml_file):
    try:
        parser = etree.XMLParser(remove_blank_text=True)
        tree = etree.parse(xml_file, parser)
        return True, tree.getroot()
    except:
        return False, None


def update_xml_file(xml_file, element):

    root = element.getroottree()

    with open(xml_file, 'wb') as xml_file_append:
        xml_file_append.write(etree.tostring(root, pretty_print=True))


def get_bgp_element(device):
    protocols = etree.SubElement(device, 'Protocols')
    bgp = etree.SubElement(protocols, 'Bgp')
    bgp.set('asn', '32934')
    bgp_groups = etree.SubElement(bgp, 'BgpPeerGroups')
    public_peering = etree.SubElement(bgp_groups, 'BgpPeerGroup')
    public_peering.set("name", 'IX')
    public_peering.set("state", 'active')
    bgp_peers = etree.SubElement(public_peering, 'BgpPeers')

    for peer in get_seattle_six_peering(13):
        if peer['asn'] == '32934':
            continue

        bgp_peer = etree.SubElement(bgp_peers, 'BgpPeer')
        bgp_peer.set('asn', str(peer['asn']))
        bgp_peer.set('ipv4', str(peer['ipaddr4']))
        bgp_peer.set('ipv6', str(peer['ipaddr6']))
        bgp_peer.set('state', 'active')



def get_physical_element(device):
    physical = etree.SubElement(device, 'Physical')
    mods = etree.SubElement(physical, 'Modules')
    mod = etree.SubElement(mods, 'Module')
    mod.set('slot', '0')
    mod.set('state', 'active')
    interfaces = etree.SubElement(mod, 'Interfaces')
    interface = etree.SubElement(interfaces, 'Interface')
    interface.set('name', 'et-0/0/1')
    interface.set('state', 'active')
    interface.set('ipv4_addr', '')
    interface.set('ipv4_cidr', '')
    interface.set('ipv6_addr', '')
    interface.set('ipv6_cidr', '')

    return mods

