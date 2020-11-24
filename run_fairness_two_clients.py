import command.command as command
import argparse

from mininet.topo import Topo
from mininet.net import Mininet
from mininet.link import TCLink

from mininet.util import dumpNodeConnections
from mininet.log import setLogLevel

from time import sleep

class CompetingClients(Topo):

    # bandwidth is in Mbits/second, delay is milliseconds by default, loss is percentage
    def build(self, bw, delay, loss, queue):
        base = self.addHost('base')
        algo = self.addHost('algo')
        server = self.addHost('server')
        switch = self.addSwitch('sw1')
        self.addLink(base, switch, cls=TCLink, bw=bw, delay=delay, loss=loss, max_queue_size=queue)
        self.addLink(algo, switch, cls=TCLink, bw=bw, delay=delay, loss=loss, max_queue_size=queue)
        self.addLink(server, switch, cls=TCLink, bw=bw, delay=delay, loss=loss, max_queue_size=queue)

class Setup:
    def __init__(self, algo_cmd, base_cmd, tag):
        self.algo = algo_cmd
        self.base = base_cmd
        self.tag = tag

    def run_experiment(self, bw, delay, loss, queue, how_long):
        setLogLevel('info')

        topo = CompetingClients(bw=bw, delay=delay, loss=loss, queue=queue)
        net = Mininet(topo)
        net.start()
        dumpNodeConnections(net.hosts)
        net.pingAll()
        # net.iperf()

        base = net.get('base')
        algo = net.get('algo')
        server = net.get('server')
        switch = net.get('sw1')
        print('SERVER IS RUNNING ON %s' % server.IP())

        base_client_cmd = self.base.get_mininet_client_cmd(server.IP(), expt_tag=self.tag)
        algo_client_cmd = self.algo.get_mininet_client_cmd(server.IP(), expt_tag=self.tag)
        base_server_cmd = self.base.get_mininet_server_cmd(expt_tag=self.tag)
        algo_server_cmd = self.algo.get_mininet_server_cmd(expt_tag=self.tag)

        print('RUNNING CMD ON BASE: %s' % base_client_cmd)
        print('RUNNING CMD ON ALGO: %s' % algo_client_cmd)
        print('RUNNING CMD ON SERVER: %s' % base_server_cmd)
        print('RUNNING CMD ON SERVER: %s' % algo_server_cmd)

        # Have the algo start first, then stop and see if base recovers
        server.cmd(algo_server_cmd)
        server.cmd(base_server_cmd)
        algo.cmd(algo_client_cmd)
        base.cmd(base_client_cmd)
        slack = 5 # cut some slack to have all printouts
        sleep(how_long/2 + slack)
        algo.stop()
        sleep(how_long/2 - slack + 1)
        net.stop()

def run_test(setups):
    bw, delay, loss, queue, how_long = 32, 32, 0, '500kb', 120

    for setup in setups:
        setup.run_experiment(bw, delay, loss, queue, how_long)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Run PCC tests")
    parser.add_argument('--rl', '-rl', help='path to reinforcement-learning repo', required=True)
    parser.add_argument('--model', '-m', help='path to model', required=True)
    parser.add_argument('--aurora', '-au', help='path to aurora root', required=True)
    parser.add_argument('--vivace', '-vi', help='path to vivace root', default='./')
    parser.add_argument('--log', '-l', help='where to store log files', default='./testing_logs')
    args = parser.parse_args()

    aurora_algo_cmd = command.AuroraCmd('aurora-algo', path=args.aurora, rlpath=args.rl, model_path=args.model, log_path=args.log, server_port=9001)
    aurora_base_cmd = command.AuroraCmd('aurora-base', path=args.aurora, rlpath=args.rl, model_path=args.model, log_path=args.log, server_port=9002)
    vivace_algo_cmd = command.VivaceCmd('vivace-algo', args.vivace, log_path=args.log, server_port=9101)
    vivace_base_cmd = command.VivaceCmd('vivace-base', args.vivace, log_path=args.log, server_port=9102)

    cubic_fulltime_iperf_cmd = command.CubicIperfCmd('cubic_fulltime',version=3, log_path=args.log, lifetime=120, server_port=5202)
    cubic_halftime_iperf_cmd = command.CubicIperfCmd('cubic_halftime',version=3, log_path=args.log, lifetime=60, server_port=5203) # end earlier

    aurora_vs_aurora = Setup(algo_cmd=aurora_algo_cmd, base_cmd=aurora_base_cmd, tag='aurora-vs-aurora')
    vivace_vs_vivace = Setup(algo_cmd=vivace_algo_cmd, base_cmd=vivace_base_cmd, tag='vivace-vs-vivace')
    cubic_vs_cubic = Setup(algo_cmd=cubic_halftime_iperf_cmd, base_cmd=cubic_fulltime_iperf_cmd, tag='cubic-vs-cubic')
    aurora_vs_cubic = Setup(algo_cmd=aurora_algo_cmd, base_cmd=cubic_fulltime_iperf_cmd, tag='aurora-vs-cubic')
    cubic_vs_aurora = Setup(base_cmd=aurora_algo_cmd, algo_cmd=cubic_halftime_iperf_cmd, tag='cubic-vs-aurora')
    aurora_vs_vivace = Setup(algo_cmd=aurora_algo_cmd, base_cmd=vivace_base_cmd, tag='aurora-vs-vivace')
    vivace_vs_aurora = Setup(algo_cmd=vivace_algo_cmd, base_cmd=aurora_base_cmd, tag='vivace-vs-aurora')
    vivace_vs_cubic = Setup(algo_cmd=vivace_algo_cmd, base_cmd=cubic_fulltime_iperf_cmd, tag='vivace-vs-cubic')
    cubic_vs_vivace = Setup(base_cmd=vivace_algo_cmd, algo_cmd=cubic_halftime_iperf_cmd, tag='cubic-vs-vivace')

    run_test([aurora_vs_aurora, vivace_vs_vivace, cubic_vs_cubic,
              aurora_vs_cubic, cubic_vs_aurora, aurora_vs_vivace,
              vivace_vs_aurora, vivace_vs_cubic, cubic_vs_vivace])
