import pandas as pd

import os
import re
import json

warning_color = '\033[93m'
end_color = '\033[0m]'

class FileData:
    '''Encapsulate (parsed) contents of log file and its metadata'''
    '''Data contains some of the following fields:
       - time
       - rtt
       - cumulative_pkts_sent
       - cumulative_pkts_lost
       - num_bytes_sent
       - num_retransmits
       - snd_cwnd
    '''

    def __init__(self, filename):
        self.name = ''
        self.meta = dict()
        self.contents = pd.DataFrame()
        self._parse(filename)

    def _parse_pcc_sender_trace(self, file):
        rate_rtt_sent_lost = []
        with open(file) as f:
            # print('Opening file %s' % file)
            time = 0
            for line in f.readlines():
                line = line.rstrip('\n')
                columns = re.split('\t+', line)
                if len(columns) == 5:
                    _, rate, rtt, sent, lost = columns
                    # print('rate (Mbps): %s, rtt (ms): %s, sent: %s, lost: %s' % (rate, rtt, sent, lost))
                    rate_rtt_sent_lost.append((time, rate, rtt, sent, lost))
                    time = time + 1 # time measured in seconds
        rate_rtt_sent_lost = rate_rtt_sent_lost[1:] # drop the column labels
        if rate_rtt_sent_lost == []:
            print(warning_color + 'WARNING: Parsing %s gave no results'  % file + end_color)
        result = [{'time': time,
                   'rate': float(rate), # in Mbits/second
                   'rtt': float(rtt), # in milliseconds
                   'cumulative_pkts_sent': int(sent),
                   'cumulative_pkts_lost': int(lost)}
                  for (time, rate, rtt, sent, lost) in rate_rtt_sent_lost]
        self.contents = pd.DataFrame(data=result)

    def _parse_iperf(self, file):
        with open(file) as f:
            try:
                contents = json.load(f)
                # Sample only the first stream from each interval
                streams = [interval['streams'][0] for interval in contents['intervals']]
                data = [ {'time': int(stream['start']),
                          'rate': stream['bits_per_second']/1000000,
                          'rtt': stream['rtt'],
                          'num_bytes_sent': stream['bytes'], # within interval, not cumulative
                          'num_retransmits': stream['retransmits'],
                          'snd_cwnd': stream['snd_cwnd'] }
                         for stream in streams]
                self.contents = pd.DataFrame(data)
            except ValueError:
                print(warning_color + 'WARNING: Cannot parse %s as JSON' % file + end_color)

    def _parse(self, filename):
        'Expect filename to be of the form key1:value1--key2:value2--<etc>.txt.'

        self.name = filename
        dirname, just_filename = os.path.split(filename)
        without_ext = os.path.splitext(just_filename)[0]
        pairs = [kv.split(':') for kv in without_ext.split('--') if len(kv.split(':')) == 2]
        for [x,y] in pairs:
            self.meta[x] = y

        if 'method' in self.meta:
            if self.meta['method'].find('iperf') >= 0:
                print('Parsing %s as iperf' % filename)
                self._parse_iperf(filename)
            elif self.meta['method'].find('aurora') >= 0 or self.meta['method'].find('vivace') >= 0:
                print('Parsing %s as aurora/vivace' % filename)
                self._parse_pcc_sender_trace(filename)
            else:
                print('WARNING: %s cannot be parsed' % filename)
        else:
            print('WARNING: %s cannot be parsed' % filename)

    def get_filename(self):
        return self.name

    def get_method(self):
        return self.meta['method']

    def get_experiment_tag(self):
        return self.meta['expt']

    def get_contents(self):
        'Return the DataFrame holding file contents'
        return self.contents
