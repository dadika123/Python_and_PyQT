"""
1. Написать функцию host_ping(), в которой с помощью утилиты ping
будет проверяться доступность сетевых узлов.
Аргументом функции является список, в котором каждый сетевой узел
должен быть представлен именем хоста или ip-адресом.
В функции необходимо перебирать ip-адреса и проверять
их доступность с выводом соответствующего сообщения
(«Узел доступен», «Узел недоступен»). При этом ip-адрес
сетевого узла должен создаваться с помощью функции ip_address().
"""

from ipaddress import ip_address
from socket import gethostbyname
from subprocess import Popen, PIPE
import platform

import chardet


def host_ping(hosts_lst: list, need_print: bool = True) -> list:
    """
    Pings each host in the given list and returns a list with ipaddress objects and ping status.
    :param hosts_lst: list of hosts (list of strings)
    :param need_print: enable/disable builtin print
    :return: list of tuples with first value being an ipaddress object and second being a boolean representing the
    reachability of the host.
    """
    checked_hosts = []
    param = '-n' if platform.system().lower() == 'windows' else '-c'
    for host in hosts_lst:
        if type(host) is not str:
            raise ValueError(f'The passed object in the list must be of a str type. {type(host)} was given.')
        process = Popen(['ping', '-t2', param, '1', host], stdout=PIPE, stderr=PIPE)
        data, err = process.communicate()
        result = chardet.detect(data)
        result_decoded = data.decode(result['encoding'])
        is_reachable = False if "unreachable" in result_decoded else True
        ip = ip_address(gethostbyname(host))
        checked_hosts.append((ip, is_reachable))
        ip_str = str(ip)
        if need_print:
            print(f'Host {host if host == ip_str else (host + " (" + ip_str + ")")} is '
                  f'{"" if is_reachable else "un"}reachable')
    return checked_hosts


if __name__ == '__main__':
    hosts = ['google.com', 'susu.ru', 'tum.de', '192.168.178.30', '192.168.178.233']
    host_ping(hosts)
    # Host google.com (142.250.181.206) is reachable
    # Host susu.ru (37.75.250.11) is reachable
    # Host tum.de (129.187.255.151) is reachable
    # Host 192.168.178.30 is reachable
    # Host 192.168.178.233 is unreachable