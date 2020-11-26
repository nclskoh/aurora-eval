import command.command as command
import argparse

from mininet.topo import Topo
from mininet.net import Mininet
from mininet.link import TCLink

from mininet.util import dumpNodeConnections
from mininet.log import setLogLevel

from time import sleep

# Parameters from NIPS 2018 "Internet Congestion Control via Deep Reinforcement Learning"
# bw, delay, loss, queue, how_long = 32, 32, 0, '500kb', 120

bw, delay, loss, queue, how_long = 32, 32, 0, None, 120

class CompetingClients(Topo):

    def build(self, bw, delay, loss, queue, clients):
        switch = self.addSwitch('sw1')
        for client in clients:
            host = self.addHost(client)
            self.addLink(host, switch, cls=TCLink, bw=bw, delay=delay, loss=loss, max_queue_size=queue)
        server = self.addHost('server')
        self.addLink(server, switch, cls=TCLink, bw=bw, delay=delay, loss=loss, max_queue_size=queue)

class Setup:
    'Run many sets of clients and servers '

    def __init__(self, cmd_generator, tag):
        self.cmd_generator = cmd_generator
        self.tag = tag

    def run_experiment(self, num_parties, bw, delay, loss, queue):
        setLogLevel('info')

        clients = ['client-%d' % i for i in range(num_parties)]
        topo = CompetingClients(bw=bw, delay=delay, loss=loss, queue=queue, clients=clients)

        net = Mininet(topo)
        net.start()
        dumpNodeConnections(net.hosts)
        net.pingAll()
        # net.iperf()

        server = net.get('server')
        print('SERVER IS RUNNING ON %s' % server.IP())

        client_cmd = [None for _ in range(num_parties)]
        server_cmd = [None for _ in range(num_parties)]

        for i in range(num_parties):
            client = net.get(clients[i])
            cmd = self.cmd_generator(i)
            client_cmd[i] = cmd.get_mininet_client_cmd(server.IP(), expt_tag=self.tag)
            server_cmd[i] = cmd.get_mininet_server_cmd(expt_tag=self.tag)

        for cmd in server_cmd:
            print('RUNNING CMD ON SERVER: %s' % cmd)
            server.cmd(server_cmd)

        for cmd in client_cmd:
            net.get(clients[i]).cmd(cmd)
            print('RUNNING CMD ON CLIENT: %s' % cmd)

        slack = 5
        sleep(how_long + slack)
        net.stop()

def aurora_cmd(idx):
    name = 'aurora-%d' % idx
    port_num = 9000 + idx
    cmd = command.AuroraCmd(name, path=args.aurora, rlpath=args.rl, model_path=args.model, log_path=args.log, server_port=port_num)
    return cmd

def vivace_cmd(idx):
    name = 'vivace-%d' % idx
    port_num = 9100 + idx
    cmd = command.VivaceCmd(name, args.vivace, log_path=args.log, server_port=port_num)
    return cmd

def cubic_cmd(idx):
    name = 'cubic-%d' % idx
    port_num = 5200 + idx
    cmd = command.CubicIperfCmd(name,version=3, log_path=args.log, lifetime=how_long, server_port=port_num)
    return cmd

def run_test(num):

    tag = 'intrafairness-%d-clients' % num
    aurora_setup = Setup(cmd_generator=aurora_cmd, tag=tag)
    vivace_setup = Setup(cmd_generator=vivace_cmd, tag=tag)
    cubic_setup = Setup(cmd_generator=cubic_cmd, tag=tag)

    aurora_setup.run_experiment(num, bw, delay, loss, queue)
    vivace_setup.run_experiment(num, bw, delay, loss, queue)
    cubic_setup.run_experiment(num, bw, delay, loss, queue)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Run PCC tests")
    parser.add_argument('--rl', '-rl', help='path to reinforcement-learning repo', required=True)
    parser.add_argument('--model', '-m', help='path to model', required=True)
    parser.add_argument('--aurora', '-au', help='path to aurora root', required=True)
    parser.add_argument('--vivace', '-vi', help='path to vivace root', default='./')
    parser.add_argument('--log', '-l', help='where to store log files', default='./testing_logs')
    parser.add_argument('--num', '-n', help='number of parties', default=None)
    args = parser.parse_args()

    if args.num is not None:
        run_test(int(args.num))
    else:
        for n in range(1, 9):
            run_test(n)
