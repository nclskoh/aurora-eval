import command.command as command
import argparse

from mininet.topo import Topo
from mininet.net import Mininet
from mininet.link import TCLink, TCIntf

from mininet.util import dumpNodeConnections, custom
from mininet.log import setLogLevel

from time import sleep

class Setup:
    def __init__(self, cmd):
        self.cmd = cmd

    def run_experiment(self, how_long, base=30, delta=10, swap_interval=10):
        setLogLevel('info')

        flag = 1

        intf = custom(TCIntf, bw=base + 2 * delta)
        net = Mininet(intf=intf)
        client = net.addHost('client')
        server = net.addHost('server')
        net.addLink(client, server)
        client_intf, server_intf = client.connectionsTo(server)[0]
        server_intf.config(bw=base + (flag * delta))
        print('Server throttled at %i Mbps' % (base + (flag * delta)))

        net.start()
        dumpNodeConnections(net.hosts)
        net.pingAll()
        # net.iperf()

        print('SERVER IS RUNNING ON %s' % server.IP())

        client_cmd = self.cmd.get_mininet_client_cmd(server.IP(), expt_tag='figure3')
        server_cmd = self.cmd.get_mininet_server_cmd(expt_tag='figure3')

        print('RUNNING CMD ON CLIENT: %s' % client_cmd)
        print('RUNNING CMD ON SERVER: %s' % server_cmd)

        server.cmd(server_cmd)
        client.cmd(client_cmd)

        # Change the link every swap_interval seconds
        while how_long >= swap_interval:
            sleep(swap_interval)
            flag = (-1) * flag
            client_intf, server_intf = client.connectionsTo(server)[0]
            # client_intf.config(bw=base + (flag * delta))
            server_intf.config(bw=base + (flag * delta))
            print('Network running at bandwidth %i Mbps' % (base + (flag * delta)))
            how_long = how_long - swap_interval

        net.stop()

def run_test(aurora, vivace, cubic):
    how_long, base, delta, swap_interval = 60, 30, 10, 10

    # aurora.cmd.set_utility('vivace')
    # aurora.cmd.set_history_len(10)
    # aurora.run_experiment(how_long)

    aurora.cmd.set_utility('linear')
    aurora.cmd.set_history_len(10)
    aurora.run_experiment(how_long, base=base, delta=delta, swap_interval=swap_interval)

    cubic.cmd.set_lifetime(how_long)
    cubic.run_experiment(how_long, base=base, delta=delta, swap_interval=swap_interval)
    vivace.run_experiment(how_long, base=base, delta=delta, swap_interval=swap_interval)

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
    cubic_iperf_cmd = command.CubicIperfCmd(version=3, log_path=args.log, lifetime=60)

    aurora_setup = Setup(aurora_cmd)
    vivace_setup = Setup(vivace_cmd)
    cubic_iperf_setup = Setup(cubic_iperf_cmd)
    run_test(aurora_setup, vivace_setup, cubic_iperf_setup)
