import jsonrpclib


def run_icmp_command(dslam_id, icmp_type, params=None):
    c = jsonrpclib.Server('http://172.28.246.134:7070')
    return c.run_icmp_command(dslam_id, icmp_type, params)