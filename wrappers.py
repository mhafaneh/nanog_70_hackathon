import jinja2
import pexpect
import requests


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


def get_peering_db_request():
