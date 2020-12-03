from parse.filedata import FileData
from util import *

import matplotlib.pyplot as plt
import matplotlib.backends.backend_pdf as pdf
import pandas as pd
from statistics import mean

import argparse
import os

def compute_fairness(rates):
    mean_rate = mean(rates)
    mean_square = mean([rate * rate for rate in rates])
    mean_square = mean_square if mean_square > 0 else mean_square + 0.00001 # deal with 0
    jain = (mean_rate * mean_rate) / mean_square
    return jain

def plot_fairness(data, output_filename):
    output = pdf.PdfPages(output_filename)

    fig, ax = plt.subplots()
    ax.set_xlabel('Number of flows')
    ax.set_ylabel('Fairness Index')
    ax.set_title('Fairness Index vs Number of flows')

    names = []
    for method in data.keys():
        label = legend_name(method)
        d = sorted(data[method].items())
        print(d)
        ax.plot(*zip(*d), marker='x', color=color(label, names))
        names.append(label)

    ax.legend(names, loc='upper right')
    output.savefig(fig)
    output.close()

def fairness_of_series(rate_columns, verbose=False, label=None):
    label_prefix = '%s: ' % label if label != None else ''
    fairness_idx = dict()
    for time in rate_columns['0'].keys(): # assume all rate data share the same times
        try:
            rates = [d[time]['rate'] for d in rate_columns.values()]
        except KeyError:
            print_warning('%sTime %s not found in some log' % (label_prefix, time))
        fairness_idx[time] = compute_fairness(rates)

    avg_fairness = mean(fairness_idx.values())

    if verbose:
        print('%sAverage fairness: %s' % (label_prefix, avg_fairness))
        print('%sFairness series: %s\n' % (label_prefix, list(fairness_idx.values())))

    return avg_fairness

def process(logs, out_dir):
    d = dict()
    for log in logs:
        num_clients = int(log.get_experiment_tag().split('-')[1])
        idx = log.get_meta('name').split('-')[1]
        method = log.get_meta('method')
        contents = log.get_contents()
        # table = contents[['time', 'rate']].rename(columns={'rate': ('rate_%s' % idx)})

        if method not in d:
            d[method] = dict()
        if num_clients not in d[method]:
            d[method][num_clients] = dict()

        # d[method][num_clients] = d[method][num_clients].merge(table, on='time')

        d[method][num_clients][idx] = contents[['time', 'rate']].set_index('time').T.to_dict()

    fairness_result = { method:
                        {num_clients: fairness_of_series(d[method][num_clients],
                                                         verbose=False,
                                                         label='%s-%s' % (method, num_clients))
                         for num_clients in d[method].keys()}
                        for method in d.keys() }

    # pd.set_option('display.max_rows', None)
    # print(pd.DataFrame(d['aurora'][2]))

    output_filename = os.path.join(out_dir, 'intrafairness.pdf')
    print('Writing to %s' % output_filename)

    plot_fairness(fairness_result, output_filename)

def group_files_by_number(logs):
    d = { i + 1: [] for i in range(8) }
    for log in logs:
        tag = log.get_experiment_tag()
        num_clients = int(tag.split('-')[1])
        d[num_clients].append(log)
    return d

if __name__ == '__main__':
    paper = "NIPS 2018 paper (Internet Congestion Control via Deep Reinforcement Learning)"
    parser = argparse.ArgumentParser(description="Plot Figure 7 of %s" % paper)
    parser.add_argument('--dir', '-d', help='directory containing log files', required=True)
    parser.add_argument('--out', '-o', help='directory to dump output files', default='./testing_logs')
    args = parser.parse_args()
    files = [os.path.join(args.dir, f) for f in os.listdir(args.dir)
             if lookup(f,'expt').startswith('intrafairness-') and lookup(f,'host') == 'client']
    print('Opening the following files: %s' % files)

    data = [FileData(f) for f in files]
    process(data, args.out)
