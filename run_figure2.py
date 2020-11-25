import command.command as command
import argparse

from mininet.topo import Topo
from mininet.net import Mininet
from mininet.link import TCLink

from mininet.util import dumpNodeConnections
from mininet.log import setLogLevel

from time import sleep

class SingleLinkTopo(Topo):
    'Single link between client and server.'

    # bandwidth is in Mbits/second, delay is milliseconds by default, loss is percentage
    def build(self, bw, delay, loss, queue):
        client = self.addHost('client')
        server = self.addHost('server')
        self.addLink(client, server, cls=TCLink, bw=bw, delay=delay, loss=loss, max_queue_size=queue)

class Setup:
    def __init__(self, cmd):
        self.cmd = cmd

    def run_experiment(self, bw, delay, loss, queue, how_long):
        setLogLevel('info')

        topo = SingleLinkTopo(bw=bw, delay=delay, loss=loss, queue=queue)
        net = Mininet(topo)
        net.start()
        dumpNodeConnections(net.hosts)
        net.pingAll()
        # net.iperf()

        client = net.get('client')
        server = net.get('server')
        print('SERVER IS RUNNING ON %s' % server.IP())

        client_cmd = self.cmd.get_mininet_client_cmd(server.IP(), expt_tag='figure2')
        server_cmd = self.cmd.get_mininet_server_cmd(expt_tag='figure2')

        print('RUNNING CMD ON CLIENT: %s' % client_cmd)
        print('RUNNING CMD ON SERVER: %s' % server_cmd)

        server.cmd(server_cmd)
        client.cmd(client_cmd)
        sleep(how_long)
        net.stop()

def run_test(aurora, vivace, cubic3, cubic2):
    # 10-packet queue, verify units are correct
    bw, delay, loss, queue, how_long = 30, None, 1, 10, 30

    aurora.cmd.set_utility('vivace')
    aurora.cmd.set_history_len(10)
    aurora.run_experiment(bw, delay, loss, queue, how_long)

    aurora.cmd.set_utility('linear')
    aurora.cmd.set_history_len(10)
    aurora.run_experiment(bw, delay, loss, queue, how_long)

    cubic3.cmd.set_lifetime(how_long)
    cubic3.run_experiment(bw, delay, loss, queue, how_long)

    # cubic2.cmd.set_lifetime(how_long)
    # cubic2.run_experiment(bw, delay, loss, queue, how_long)

    vivace.run_experiment(bw, delay, loss, queue, how_long)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Run PCC tests")
    parser.add_argument('--rl', '-rl', help='path to reinforcement-learning repo', required=True)
    parser.add_argument('--model', '-m', help='path to model', required=True)
    parser.add_argument('--aurora', '-au', help='path to aurora root', required=True)
    parser.add_argument('--vivace', '-vi', help='path to vivace root', default='./')
    parser.add_argument('--log', '-l', help='where to store log files', default='./testing_logs')
    args = parser.parse_args()

    aurora_cmd = command.AuroraCmd('aurora', path=args.aurora, rlpath=args.rl, model_path=args.model, log_path=args.log)
    vivace_cmd = command.VivaceCmd('vivace', args.vivace, log_path=args.log)
    cubic_iperf3_cmd = command.CubicIperfCmd('cubic-iperf3', version=3, log_path=args.log, lifetime=30)
    cubic_iperf2_cmd = command.CubicIperfCmd('cubic-iperf2', version=2, log_path=args.log, lifetime=30)

    aurora_setup = Setup(aurora_cmd)
    vivace_setup = Setup(vivace_cmd)
    cubic_iperf3_setup = Setup(cubic_iperf3_cmd)
    cubic_iperf2_setup = Setup(cubic_iperf2_cmd)
    run_test(aurora_setup, vivace_setup, cubic_iperf3_setup, cubic_iperf2_setup)
