from parse.filedata import FileData
from util import *

import matplotlib.pyplot as plt
import matplotlib.backends.backend_pdf as pdf
import matplotlib.cm as cm
import pandas as pd

import argparse
import os

def plot_scatter(data, output_filename, title=None):
    output = pdf.PdfPages(output_filename)

    fig, ax = plt.subplots()
    if title is not None:
        ax.set_title(title)

    names = []
    colors = {'aurora': 'orange', 'vivace': 'green', 'iperf3_cubic': 'blue'}
    markers = {'aurora': 'x', 'vivace': 'o', 'iperf3_cubic': '^'}
    xticks = [10, 20, 30, 40, 50, 60]
    yticks = [10, 20, 30, 40, 50]
    for (method, df) in data.items():
        axes = df.plot(x='rtt', y='rate', ax=ax, kind='scatter',
                       color=colors[method],
                       grid=True,
                       xticks=xticks, yticks=yticks,
                       marker=markers[method])
        names.append(method)

    ax.set_xlabel('Average Latency (ms)')
    ax.set_ylabel('Average Throughput (Mbps)')
    ax.legend(names, loc='upper right')
    output.savefig(fig)
    output.close()

def process(logs, out_dir):
    d = dict()

    for log in logs:
        iteration = log.get_experiment_tag().split('-')[1]
        method = log.get_method()
        contents = log.get_contents()
        average_rate = contents['rate'].mean()
        average_rtt = contents['rtt'].mean()
        if method not in d:
            d[method] = pd.DataFrame()
        d[method] = d[method].append({'rate': average_rate, 'rtt': average_rtt}, ignore_index=True)

    output_filename = os.path.join(out_dir, 'figure7.pdf')
    print('Writing to %s' % output_filename)
    plot_scatter(d, output_filename)

if __name__ == '__main__':
    paper = "ICML 2019 paper (A Deep Reinforcement Learning Perspective on Internet Congestion Control)"
    parser = argparse.ArgumentParser(description="Plot Figure 7 of %s" % paper)
    parser.add_argument('--dir', '-d', help='directory containing log files', required=True)
    parser.add_argument('--out', '-o', help='directory to dump output files', default='./testing_logs')
    args = parser.parse_args()
    files = [os.path.join(args.dir, f) for f in os.listdir(args.dir)
             if lookup(f,'expt').startswith('figure7-') and lookup(f,'host') == 'client']
    print('Opening the following files: %s' % files)

    figure7_data = [FileData(f) for f in files]
    process(figure7_data, args.out)
