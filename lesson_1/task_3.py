"""
Написать функцию host_range_ping_tab(), возможности которой основаны на функции из примера 2.
Но в данном случае результат должен быть итоговым по всем ip-адресам, представленным в табличном формате
(использовать модуль tabulate). Таблица должна состоять из двух колонок
"""
from tabulate import tabulate

from task_2 import host_range_ping


def host_range_ping_tab(host_range: str):
    """
    Pings the hosts in a given range and prints the data in a table format.
    :param host_range: ip range
    :return: None
    """
    hosts = host_range_ping(host_range, need_print=False)
    results = {'Reachable': [], 'Unreachable': []}
    # Here, a regular for loop is faster than list comprehension
    for host in hosts:
        if host[1]:
            results['Reachable'].append(host[0])
        else:
            results['Unreachable'].append(host[0])
    print(tabulate(results, headers='keys', tablefmt='simple'))


if __name__ == '__main__':
    host_range = '192.168.178.0/29'
    host_range_ping_tab(host_range)
    # Reachable      Unreachable
    # -------------  -------------
    # 192.168.178.1  192.168.178.0
    #                192.168.178.2
    #                192.168.178.3
    #                192.168.178.4
    #                192.168.178.5
    #                192.168.178.6
    #                192.168.178.7