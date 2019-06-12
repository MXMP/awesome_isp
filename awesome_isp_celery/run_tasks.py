from .tasks import ping_host
import time


def print_results(results):
    return [r.result for r in results]


if __name__ == '__main__':
    hosts_to_ping = ['10.99.192.19', '10.99.192.20', '10.99.192.200']
    results = []
    for host in hosts_to_ping:
        ping_result = ping_host.delay(host)
        results.append(ping_result)

    time.sleep(5)
    print(f'Results: {", ".join([str(r.result) for r in results])}')
