from ipaddress import ip_network

from .tasks import save_host, get_model


def print_results(results):
    return [r.result for r in results]


if __name__ == '__main__':
    # Есть сетка, например 10.99.192.0/24
    network = ip_network('10.99.192.0/24')

    # берем все хосты для этой сетки и проверяем каждый является ли он коммутатором (шлем SNMP на получение
    # инфы о модели)
    hosts = network.hosts()
    for host in hosts:
        model = get_model.delay(host.compressed)
        if model:
            save_host.delay(host.compressed, model, 'ok', {})

    # если это действительно коммутатор, то кладем инфу о нем в БД
    # для всех коммутаторов нужно соорудить периодическое пингование
    # берем все коммутаторы из БД и для каждого из них спрашиваем LLDP и кладем эту инфу в БД

    # hosts_to_ping = ['10.99.192.19', '10.99.192.20', '10.99.192.200']
    # results = []
    # for host in hosts_to_ping:
    #     ping_result = ping_host.delay(host)
    #     results.append(ping_result)
    #
    # time.sleep(5)
    # print(f'Results: {", ".join([str(r.result) for r in results])}')
