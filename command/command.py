import os

class Log:
    'Logging discipline: log file follows key-value discipline of the form key:value.'
    'TODO: Need to refactor logging discipline below...'

    def __init__(self, log_path):
        self.path = log_path

    def make_filename(self, expt_tag, description):
        filename = os.path.join(self.path, 'expt:%s--%s.txt' % (expt_tag, description))
        return filename

    def make_err_filename(self, expt_tag, description):
        filename = os.path.join(self.path, 'expt:%s--%s--stderr.txt' % (expt_tag, description))
        return filename

class Cmd:
    '''Encapsulates the server and client command to run'''
    'The log parser relies the following tags: name (for legend in graph), host, method. TODO: Enforce this at interface level.'

    def __init__(self, label, server_port):
        'Client and server descriptions are labels for respective log files generated'
        self.client_cmd = ''
        self.server_cmd = ''
        self.client_description = 'name:%s--host:client' % label
        self.server_descriptin = 'name:%s--host:server' % label
        self.server_port = server_port
        self.Log = Log('./')

    def get_client_cmd(self, server_ip):
        'Return client command that does no logging'
        'Runtime arguments like bw, delay, and loss are usually not needed, '
        'but command may use them, e.g. in its own logging'
        pass

    def get_server_cmd(self):
        'Return server command that does no logging'
        pass

    def get_client_description(self):
        return self.client_description

    def get_server_description(self):
        return self.server_description

    def get_mininet_client_cmd(self, server_ip, expt_tag):
        'Return client command that also logs results to file'

        log_file = self.log.make_filename(expt_tag, self.get_client_description())
        stderr_file = self.log.make_filename(expt_tag, self.get_client_description())
        cmd = '%s > %s 2> %s &' % (self.get_client_cmd(server_ip), log_file, stderr_file)
        return cmd

    def get_mininet_server_cmd(self, expt_tag):
        'Return server command that also logs results to file'

        log_file = self.log.make_filename(expt_tag, self.get_server_description())
        stderr_file = self.log.make_filename(expt_tag, self.get_server_description())

        cmd = '%s > %s 2> %s &' % (self.get_server_cmd(), log_file, stderr_file)
        return cmd

    def set_server_port(port):
        self.server_port = port

class AuroraCmd(Cmd):
    '''Generate commands to run Aurora PPC client and server'''

    def __init__(self,
                 label,
                 path,
                 rlpath,
                 model_path,
                 log_path,
                 utility='vivace',
                 history_len=10,
                 model_log_dir='./',
                 server_port=9000):
        rlpath = os.path.abspath(rlpath)
        model_path = os.path.abspath(model_path)

        core_path = os.path.join(path, 'src/core')
        env = 'LD_LIBRARY_PATH=%s' % core_path
        exe_path = os.path.join(path, 'src/app')
        client = os.path.join(exe_path, 'pccclient')
        server = os.path.join(exe_path, 'pccserver')

        self.pypath = os.path.join(rlpath, 'src/udt-plugins/testing')
        self.model_path = model_path
        self.history_len = history_len
        self.utility = utility
        self.model_log_dir = model_log_dir
        self.server_port = server_port
        self.client_cmd = '%s %s' % (env, client)
        self.server_cmd = '%s %s' % (env, server)
        self.client_description = 'name:%s--host:client--method:aurora' % label
        self.server_description = 'name:%s--host:server--method:aurora' % label
        self.log = Log(log_path)

    def get_client_cmd(self, server_ip):
        history = '--history=len=%s' % str(self.history_len) # Likely MI length?
        pcc_log = os.path.join(self.model_log_dir, 'pcc_log--%s.txt' % (self.get_client_description()))
        utility_logging = '--log-utility-calc-lite -log=%s' % pcc_log # should have better logging
        # utility_logging = '--log-utility-calc-lite'
        utility = '--pcc-utility-calc=%s %s' % (self.utility, utility_logging)
        rate_control = '--pcc-rate-control=python -pyhelper=loaded_client -pypath=%s --model-path=%s' % (self.pypath, self.model_path)
        cmd = '%s send %s %s %s %s %s' % (self.client_cmd, server_ip, self.server_port, rate_control, history, utility)
        return cmd

    def get_server_cmd(self):
        cmd = '%s recv %s' % (self.server_cmd, self.server_port)
        return cmd

    def set_history_len(self, history_len):
        self.history_len = history_len

    def set_utility(self, utility):
        "vivace is default ('vivace' | 'linear' | 'loss-only' | 'copa' | 'ixp')"
        self.utility = utility

    def get_client_description(self):
        return '%s--history:%s--utility:%s' % (self.client_description, self.history_len, self.utility)

    def get_server_description(self):
        return '%s--history:%s--utility:%s' % (self.server_description, self.history_len, self.utility)

class VivaceCmd(Cmd):
    '''Generate commands to run Vivace PPC client and server'''

    def __init__(self, label, path, log_path, server_port=9000):
        client_core_path = os.path.join(path, 'pcc-gradient/sender/src')
        server_core_path = os.path.join(path, 'pcc-gradient/receiver/src')

        client_env = 'LD_LIBRARY_PATH=%s' % client_core_path
        server_env = 'LD_LIBRARY_PATH=%s' % server_core_path

        # usage: gradient_descent_pcc_client server_ip
        #          server_port [factor] [step] [alpha = 4] [beta = 1] [exponent = 2.5] [poly_utility = 1]
        # usage: appserver [server_port]

        client_exe_path = os.path.join(path, 'pcc-gradient/sender/app')
        server_exe_path = os.path.join(path, 'pcc-gradient/receiver/app')

        client = os.path.join(client_exe_path, 'gradient_descent_pcc_client')
        server = os.path.join(server_exe_path, 'appserver')
        self.client_cmd = '%s %s' % (client_env, client)
        self.server_cmd = '%s %s' % (server_env, server)
        self.client_description = 'name:%s--host:client--method:vivace' % label
        self.server_description = 'name:%s--host:server--method:vivace' % label
        self.log = Log(log_path)
        self.server_port = server_port

    def get_client_cmd(self, server_ip):
        # For some reason, running the command WITHOUT directing stderr leads to 0 throughput.
        # Need to figure out why...
        # cmd = '%s %s 9000 > %s 2> %s &' % (self.client_cmd, server_ip)
        cmd = '%s %s %s' % (self.client_cmd, server_ip, self.server_port)
        return cmd

    def get_server_cmd(self):
        cmd = '%s %s' % (self.server_cmd, self.server_port)
        return cmd

class CubicIperfCmd(Cmd):
    '''Generate commands to run Cubic IPerf client and server'''

    def __init__(self, label, log_path, lifetime, version=3, server_port=5201):
        self.client_cmd = ''
        self.server_cmd = ''
        self.client_description = 'name:%s--host:client--method:iperf%s_cubic' % (label, version)
        self.server_description = 'name:%s--host:server--method:iperf%s_cubic' % (label, version)
        self.version = version
        self.log = Log(log_path)
        self.lifetime = lifetime
        self.server_port = server_port

    def get_client_cmd(self, server_ip):
        if self.version == 3:
            cmd = 'iperf3 -c %s -p %s -i 1 -C cubic -t %i -J' % (server_ip, self.server_port, self.lifetime)
        else:
            cmd = 'iperf -c %s -p %s -i 1 -f m -e -Z cubic -t %i' % (server_ip, self.server_port, self.lifetime)
        return cmd

    def get_server_cmd(self):
        if self.version == 3:
            cmd = 'iperf3 -s -J -p %s' % self.server_port
        else:
            cmd = 'iperf -s -p %s' % self.server_port
        return cmd

    def set_version(self, version):
        self.version = version

    def set_lifetime(self, lifetime):
        self.lifetime = lifetime
