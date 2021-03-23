from flask import Flask, Response, render_template, url_for
import docker
from datetime import datetime

app = Flask(__name__)

def humansize(nbytes):
    suffixes = ['B', 'KB', 'MB', 'GB', 'TB', 'PB']
    i = 0
    while nbytes >= 1024 and i < len(suffixes)-1:
        nbytes /= 1024.
        i += 1
    f = ('%.2f' % nbytes).rstrip('0').rstrip('.')
    return '%s%s' % (f, suffixes[i])

def statistics(container_id):
    container = client.containers.get(container_id=container_id)
    stats = container.stats(stream=False, decode=False)

    id = stats['id'][:10]
    name = stats['name'][1:]

    memory_stats = stats['memory_stats']
    used_memory = memory_stats['usage'] - memory_stats['stats']['cache']
    available_memory = memory_stats['limit']

    precpu_stats = stats['precpu_stats']
    cpu_stats = stats['cpu_stats']
    cpu_delta = cpu_stats['cpu_usage']['total_usage'] - precpu_stats['cpu_usage']['total_usage']
    system_cpu_delta = cpu_stats['system_cpu_usage'] - precpu_stats['system_cpu_usage']
    number_cpus = cpu_stats['online_cpus']
    cpu_usage = (cpu_delta / system_cpu_delta) * number_cpus * 100.0

    network_stats = stats['networks']
    input_traffic = network_stats['eth0']['rx_bytes']
    output_traffic = network_stats['eth0']['tx_bytes']

    block_stats = stats['blkio_stats']
    if len(block_stats['io_service_bytes_recursive']) != 0:
        read_info = block_stats['io_service_bytes_recursive'][0]['value']
        write_info = block_stats['io_service_bytes_recursive'][1]['value']
    else:
        read_info = 0
        write_info = 0

    pids_stats = stats['pids_stats']
    pids = pids_stats['current']

    new_id = id + ' '

    if len(name) >= 19:
        new_name = name[:16] + '...'
    else:
        new_name = name + ((19 - len(name)) * ' ')

    new_cpu_usage = str(round(cpu_usage, 2)) + '%'
    new_cpu_usage += (7 - len(new_cpu_usage)) * ' '

    new_used_memory = humansize(used_memory)
    new_used_memory += (8 - (len(new_used_memory))) * ' '

    new_available_memory = humansize(available_memory)
    new_available_memory += (8 - (len(new_available_memory))) * ' '

    memory_usage = str(round(used_memory / available_memory * 100, 2)) + '%'
    memory_usage += (7 - (len(memory_usage))) * ' '

    new_input_traffic = humansize(input_traffic)
    new_input_traffic += (8 - len(new_input_traffic)) * ' '

    new_output_traffic = humansize(output_traffic)
    new_output_traffic += (8 - len(new_output_traffic)) * ' '

    new_read_info = humansize(read_info)
    new_read_info += (8 - len(new_read_info)) * ' '

    new_write_info = humansize(write_info)
    new_write_info += (8 - len(new_write_info)) * ' '

    return new_id, new_name, new_cpu_usage, new_used_memory, new_available_memory, memory_usage, new_input_traffic, new_output_traffic, new_read_info, new_write_info, pids

client = docker.from_env()

@app.route('/')
def index():
    info = [statistics(container.id) for container in client.containers.list()]
    title = "Docker Statistics"
    return render_template('index.html', title=title, info=info)

@app.route('/info')
def info():
    info = [statistics(container.id) for container in client.containers.list()]
    title = "Docker Info"
    return render_template('info.html', title=title, info=info)

# print([statistics(container.id) for container in client.containers.list()])
if __name__ == "__main__":
    app.run(host= '46.101.225.182', debug=True, threaded=True)
