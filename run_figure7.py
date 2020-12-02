import command.command as command
import argparse

from mininet.topo import Topo
from mininet.net import Mininet
from mininet.link import TCLink, TCIntf

from mininet.util import dumpNodeConnections, custom
from mininet.log import setLogLevel

from time import sleep
import random

class Setup:
    def __init__(self, cmd):
        self.cmd = cmd

    def run_experiment(self, iter_idx, how_long, min_bw=16, max_bw=32, interval=10):
        setLogLevel('info')

        intf = custom(TCIntf, bw=max_bw)
        net = Mininet(intf=intf)
        client = net.addHost('client')
        server = net.addHost('server')
        net.addLink(client, server)
        client_intf, server_intf = client.connectionsTo(server)[0]

        bw = random.randint(min_bw, max_bw)
        server_intf.config(bw=bw)
        client_intf.config(bw=bw)
        print('Network at %i Mbps' % bw)

        net.start()
        dumpNodeConnections(net.hosts)
        net.pingAll()
        # net.iperf()

        print('SERVER IS RUNNING ON %s' % server.IP())

        client_cmd = self.cmd.get_mininet_client_cmd(server.IP(), expt_tag='figure7-%s' % iter_idx)
        server_cmd = self.cmd.get_mininet_server_cmd(expt_tag='figure7-%s' % iter_idx)

        print('RUNNING CMD ON CLIENT: %s' % client_cmd)
        print('RUNNING CMD ON SERVER: %s' % server_cmd)

        server.cmd(server_cmd)
        client.cmd(client_cmd)

        # Change the link every interval seconds
        while how_long >= interval:
            sleep(interval)
            bw = random.randint(min_bw, max_bw)
            client_intf, server_intf = client.connectionsTo(server)[0]
            server_intf.config(bw=bw)
            client_intf.config(bw=bw)
            print('Network at %i Mbps' % bw)
            how_long = how_long - interval

        net.stop()

def run_test(aurora, vivace, cubic3):
    how_long, min_bw, max_bw, interval = 120, 16, 32, 5
    num_iters = 10

    aurora.cmd.set_utility('vivace')
    aurora.cmd.set_history_len(10)

    cubic3.cmd.set_lifetime(how_long)

    for i in range(num_iters):
        aurora.run_experiment(i, how_long, min_bw=min_bw, max_bw=max_bw, interval=interval)
        cubic3.run_experiment(i, how_long, min_bw=min_bw, max_bw=max_bw, interval=interval)
        vivace.run_experiment(i, how_long, min_bw=min_bw, max_bw=max_bw, interval=interval)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Run experiments pertaining to Figure 3")
    parser.add_argument('--rl', '-rl', help='path to reinforcement-learning repo', required=True)
    parser.add_argument('--model', '-m', help='path to model', required=True)
    parser.add_argument('--aurora', '-au', help='path to aurora root', required=True)
    parser.add_argument('--vivace', '-vi', help='path to vivace root', default='./')
    parser.add_argument('--log', '-l', help='where to store log files', default='./testing_logs')
    args = parser.parse_args()

    aurora_cmd = command.AuroraCmd('aurora', path=args.aurora, rlpath=args.rl, model_path=args.model, log_path=args.log)
    vivace_cmd = command.VivaceCmd('vivace', args.vivace, log_path=args.log)
    cubic_iperf3_cmd = command.CubicIperfCmd('cubic3', version=3, log_path=args.log, lifetime=60)

    aurora_setup = Setup(aurora_cmd)
    vivace_setup = Setup(vivace_cmd)
    cubic_iperf3_setup = Setup(cubic_iperf3_cmd)
    run_test(aurora_setup, vivace_setup, cubic_iperf3_setup)
