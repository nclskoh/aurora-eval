import command.command as command
import argparse

from mininet.topo import Topo
from mininet.net import Mininet
from mininet.link import TCLink, TCIntf

from mininet.util import dumpNodeConnections, custom
from mininet.log import setLogLevel

from time import sleep
import random

# default_bw, default_delay, default_loss, default_queue = 30, None, None, None
default_bw, default_delay, default_loss, default_queue = 30, 30, 0, 1000 # paper defaults
default_run_length = 120 # 2 minutes per paper

class SingleLinkTopo(Topo):
    'Single link between client and server.'

    # bandwidth is in Mbits/second, delay is milliseconds by default, loss is percentage
    def build(self, bw, delay, loss, queue):
        client = self.addHost('client')
        server = self.addHost('server')
        self.addLink(client, server, cls=TCLink, bw=bw, delay=delay, loss=loss, max_queue_size=queue)

class Setup:
    def __init__(self, cmd, bw, delay, loss, queue):
        'Set network parameter defaults (controls) for the setup'
        self.cmd = cmd
        self.params = dict()
        self.params['bw'] = bw
        self.params['delay'] = delay
        self.params['loss'] = loss
        self.params['queue'] = queue

    def _run(self, how_long, bw=None, delay=None, loss=None, queue=None, tag=None):
        'Run single-link network between server and client at set parameters '
        'and write to file with tag'

        bw = self.params['bw'] if bw is None else bw
        delay = self.params['delay'] if delay is None else delay
        loss = self.params['loss'] if loss is None else loss
        queue = self.params['queue'] if queue is None else queue

        topo = SingleLinkTopo(bw, delay, loss, queue)
        print('NETWORK IS SET AT (%s Mbps, %s ms, %s percent, %s packets)' % (bw, delay, loss, queue))
        net = Mininet(topo)
        net.start()
        dumpNodeConnections(net.hosts)
        net.pingAll()
        # net.iperf()

        client = net.get('client')
        server = net.get('server')
        print('SERVER IS RUNNING ON %s' % server.IP())

        if tag is None:
            tag = 'figure6-single--bw:%d--delay:%s--loss:%s--queue:%s' % (bw, delay, loss, queue)

        # Experiments can sometimes fail, and a possible reason is that
        # ports are not freed up fast enough.
        port = random.randrange(9000, 9100)
        self.cmd.set_server_port(port)

        client_cmd = self.cmd.get_mininet_client_cmd(server.IP(), expt_tag=tag)
        server_cmd = self.cmd.get_mininet_server_cmd(expt_tag=tag)

        print('RUNNING CMD ON CLIENT: %s' % client_cmd)
        print('RUNNING CMD ON SERVER: %s' % server_cmd)

        server.cmd(server_cmd)
        client.cmd(client_cmd)
        sleep(how_long)
        net.stop()

    def run_experiment(self, how_long, variable_data=None):
        'Run a single experiment for how_long seconds at default seconds if '
        'variable_data is not set, otherwise run a set of experiments with '
        'variable varying over a set of values according to variable_data.'

        if variable_data is None:
            # just run at defaults
            self._run(how_long)
        else:
            variable, params = variable_data
            for param in params:
                tag = 'figure6-%s-%d' % (variable, param)
                if variable == 'bw':
                    self._run(how_long, bw=param, tag=tag)
                elif variable == 'delay':
                    self._run(how_long, delay=param, tag=tag)
                elif variable == 'loss':
                    self._run(how_long, loss=param, tag=tag)
                elif variable == 'queue':
                    self._run(how_long, queue=param, tag=tag)

def run_sweep(aurora, vivace, cubic3, variable):

    # Run multiple experiments with these as controls
    bw, delay, loss, queue = default_bw, default_delay, default_loss, default_queue
    how_long = default_run_length

    aurora = Setup(aurora_cmd, bw=bw, delay=delay, loss=loss, queue=queue)
    vivace = Setup(vivace_cmd, bw=bw, delay=delay, loss=loss, queue=queue)
    cubic3 = Setup(cubic_iperf3_cmd, bw=bw, delay=delay, loss=loss, queue=queue)

    aurora.cmd.set_utility('vivace')
    aurora.cmd.set_history_len(10)
    cubic3.cmd.set_lifetime(how_long)

    if variable == 'bw':
        intervals = [1, 8, 16, 32, 64, 96, 128]
    elif variable == 'delay':
        intervals = [1, 16, 32, 64, 128, 256, 384, 512]
    elif variable == 'loss':
        intervals = [1, 2, 3, 4, 5, 6, 7, 8]
    elif variable == 'queue':
        intervals = [1, 100, 500, 1000, 2500, 5000, 7500, 10000]
    else:
        raise ValueError()

    aurora.run_experiment(how_long, variable_data=(variable, intervals))
    cubic3.run_experiment(how_long, variable_data=(variable, intervals))
    vivace.run_experiment(how_long, variable_data=(variable, intervals))

def run_single_test(aurora_cmd, vivace_cmd, cubic_cmd, bw, delay, loss, queue):
    how_long = default_run_length

    aurora = Setup(aurora_cmd, bw=bw, delay=delay, loss=loss, queue=queue)
    vivace = Setup(vivace_cmd, bw=bw, delay=delay, loss=loss, queue=queue)
    cubic3 = Setup(cubic_cmd, bw=bw, delay=delay, loss=loss, queue=queue)

    aurora.cmd.set_utility('vivace')
    aurora.cmd.set_history_len(10)
    cubic3.cmd.set_lifetime(how_long)

    aurora.run_experiment(how_long)
    cubic3.run_experiment(how_long)
    vivace.run_experiment(how_long)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Run experiments pertaining to Figure 6")
    parser.add_argument('--rl', '-rl', help='path to reinforcement-learning repo', required=True)
    parser.add_argument('--model', '-m', help='path to model', required=True)
    parser.add_argument('--aurora', '-au', help='path to aurora root', required=True)
    parser.add_argument('--vivace', '-vi', help='path to vivace root', default='./')
    parser.add_argument('--log', '-l', help='where to store log files', default='./testing_logs')
    parser.add_argument('--all-bw', help='run bandwidth test (fig 6a)', default=False, action='store_true')
    parser.add_argument('--all-delay', help='run latency test (fig 6b)', default=False, action='store_true')
    parser.add_argument('--all-queue', help='run bandwidth test (fig 6c)', default=False, action='store_true')
    parser.add_argument('--all-loss', help='run latency test (fig 6d)', default=False, action='store_true')
    parser.add_argument('--all', help='run all tests in fig 6d', default=False, action='store_true')
    parser.add_argument('--bw', help='run a single setup with bw', default=None)
    parser.add_argument('--delay', help='run a single setup with delay', default=None)
    parser.add_argument('--queue', help='run a single setup with queue', default=None)
    parser.add_argument('--loss', help='run a single setup with loss', default=None)

    args = parser.parse_args()

    aurora_cmd = command.AuroraCmd('aurora', path=args.aurora, rlpath=args.rl,
                                   model_path=args.model, log_path=args.log)
    vivace_cmd = command.VivaceCmd('vivace', args.vivace, log_path=args.log)
    cubic_iperf3_cmd = command.CubicIperfCmd('cubic3', version=3,
                                             log_path=args.log, lifetime=30)

    if args.all:
        args.all_bw, args.all_delay, args.all_queue, args.all_loss = True, True, True, True

    single_selected = args.bw or args.delay or args.queue or args.loss
    all_selected = args.all_bw or args.all_delay or args.all_queue or args.all_loss

    if (single_selected and all_selected) is True or (single_selected or all_selected) is False:
        all_usage = '(--all-bw | --all-delay | --all-queue | --all-loss | --all)'
        single_usage = '(--bw BW --delay DELAY --queue QUEUE --loss LOSS), leave blank for default'
        print('Choose %s or %s.' % (all_usage, single_usage))
        exit(0)

    if args.all_bw is True:
        run_sweep(aurora_cmd, vivace_cmd, cubic_iperf3_cmd, variable='bw')
    if args.all_delay is True:
        run_sweep(aurora_cmd, vivace_cmd, cubic_iperf3_cmd, variable='delay')
    if args.all_queue is True:
        run_sweep(aurora_cmd, vivace_cmd, cubic_iperf3_cmd, variable='queue')
    if args.all_loss is True:
        run_sweep(aurora_cmd, vivace_cmd, cubic_iperf3_cmd, variable='loss')

    if single_selected:
        bw = int(args.bw) if args.bw is not None else default_bw
        delay = int(args.delay) if args.delay is not None else default_delay
        loss = float(args.loss) if args.loss is not None else default_loss
        queue = int(args.queue) if args.queue is not None else default_queue

        print('Running single test: bw: %s, delay: %s, loss: %s, queue: %s' % (bw, delay, loss, queue))

        run_single_test(aurora_cmd, vivace_cmd, cubic_iperf3_cmd, bw, delay, loss, queue)
