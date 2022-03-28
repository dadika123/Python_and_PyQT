"""
2. Написать функцию host_range_ping() для перебора ip-адресов из заданного диапазона.
Меняться должен только последний октет каждого адреса.
По результатам проверки должно выводиться соответствующее сообщение.
"""
from ipaddress import ip_network

from task_1 import host_ping


def host_range_ping(host_range: str, need_print: bool = True) -> list:
    """
    Pings the hosts in a given range.
    :param host_range: ip range
    :param need_print: enable/disable builtin print
    :return: list of tuples with first value being an ipaddress object and second being a boolean representing the
    reachability of the host.
    """
    hosts = []
    if '/' in host_range:
        hosts = [str(ip) for ip in ip_network(host_range)]
    elif '-' in host_range:
        start_ip, end = [item.strip() for item in host_range.split('-')]
        if '.' in end:
            end = end.rsplit('.', 1)[-1]
        start = int(start_ip.rsplit('.', 1)[-1])
        end = int(end)
        start_ip = start_ip.rsplit(".", 1)[0]
        hosts = [f'{start_ip}.{i}' for i in range(start, end + 1)]
    else:
        hosts.append(host_range)
    return host_ping(hosts, need_print)


if __name__ == '__main__':
    host_range = '192.168.178.0/29'
    host_range_ping(host_range)
    host_range = '192.168.178.0-7'
    host_range_ping(host_range)
    host_range = '192.168.178.0-192.168.178.7'
    host_range_ping(host_range)
    # 192.168.178.0: Host is unreachable
    # 192.168.178.1: Host is reachable
    # 192.168.178.2: Host is unreachable
    # 192.168.178.3: Host is unreachable
    # 192.168.178.4: Host is unreachable
    # 192.168.178.5: Host is unreachable
    # 192.168.178.6: Host is unreachable
    # 192.168.178.7: Host is unreachable