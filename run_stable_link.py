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
    def build(self, n=2, bw=100, delay='5ms', loss=0):
        client = self.addHost('client')
        server = self.addHost('server')
        self.addLink(client, server, cls=TCLink, bw=bw, delay=delay, loss=loss)

class Setup:
    'Run a server/client command pair on two hosts connected by a single link'

    def __init__(self, cmd):
        self.cmd = cmd

    def run_experiment(self, bw, delay, loss):
        setLogLevel('info')

        how_long = 40 # seconds

        topo = SingleLinkTopo(n=2, bw=bw, delay=delay, loss=loss)
        net = Mininet(topo)
        net.start()
        dumpNodeConnections(net.hosts)
        net.pingAll()

        client = net.get('client')
        server = net.get('server')
        print('SERVER IS RUNNING ON %s' % server.IP())

        client_cmd = self.cmd.get_mininet_client_cmd(server.IP(), expt_tag='single_link')
        server_cmd = self.cmd.get_mininet_server_cmd(expt_tag='single_link')

        print('RUNNING CMD ON CLIENT: %s' % client_cmd)
        print('RUNNING CMD ON SERVER: %s' % server_cmd)

        server.cmd(server_cmd)
        client.cmd(client_cmd)
        sleep(how_long)
        net.stop()

def run_test(aurora, vivace, cubic):
    'Run PCC with two directly connected hosts'

    bw, delay, loss = 100, 5, 1

    aurora.cmd.set_utility('vivace')
    aurora.cmd.set_history_len(10)
    aurora.run_experiment(bw, delay, loss)
    aurora.cmd.set_history_len(20)
    aurora.run_experiment(bw, delay, loss)

    aurora.cmd.set_utility('linear')
    aurora.cmd.set_history_len(10)
    aurora.run_experiment(bw, delay, loss)

    cubic.run_experiment(bw, delay, loss)
    vivace.run_experiment(bw, delay, loss)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Run PCC tests")
    parser.add_argument('--rl', '-rl', help='path to reinforcement-learning repo', required=True)
    parser.add_argument('--model', '-m', help='path to model', required=True)
    parser.add_argument('--aurora', '-au', help='path to aurora root', required=True)
    parser.add_argument('--vivace', '-vi', help='path to vivace root', default='./')
    parser.add_argument('--log', '-l', help='where to store log files', default='./testing_logs')
    args = parser.parse_args()

    aurora_cmd = command.AuroraCmd(path=args.aurora, rlpath=args.rl, model_path=args.model, log_path=args.log)
    vivace_cmd = command.VivaceCmd(args.vivace, log_path=args.log)
    cubic_iperf_cmd = command.CubicIperfCmd(version=3, log_path=args.log)

    aurora_setup = Setup(aurora_cmd)
    vivace_setup = Setup(vivace_cmd)
    cubic_iperf_setup = Setup(cubic_iperf_cmd)
    run_test(aurora_setup, vivace_setup, cubic_iperf_setup)
