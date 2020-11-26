from parse.filedata import FileData

import matplotlib.pyplot as plt
import matplotlib.backends.backend_pdf as pdf
import pandas as pd
from statistics import mean

import argparse
import os

warning_color = '\033[93m'
end_color = '\033[0m'

def compute_fairness(rates):
    mean_rate = mean(rates)
    mean_square = mean([rate * rate for rate in rates])
    jain = (mean_rate * mean_rate) / mean_square
    return jain

def plot_fairness(data, output_filename):
    output = pdf.PdfPages(output_filename)

    fig, ax = plt.subplots()
    ax.set_xlabel('Number of flows')
    ax.set_ylabel('Fairness Index')
    ax.set_title('Fairness Index vs Number of flows')

    method_data = data.groupby('method')

    names = []
    for method, experiments in method_data:
        series = experiments.groupby('num_clients')['rate'].aggregate(compute_fairness)
        series.plot(y='rate', ax=ax, marker='x')
        names.append(method)

    ax.legend(names, loc='lower right')
    output.savefig(fig)
    output.close()

def process(logs, out_dir):
    rows = []
    for log in logs:
        num_clients = int(log.get_experiment_tag().split('-')[1])
        idx = log.get_meta('name').split('-')[1]
        contents = log.get_contents()
        rate = contents['rate'].quantile(0.5)
        rows.append({'num_clients': num_clients, 'method': log.get_meta('method'), 'index': idx, 'rate': rate})

    df = pd.DataFrame(rows)

    output_filename = os.path.join(out_dir, 'intrafairness.pdf')
    print('Writing to %s' % output_filename)
    plot_fairness(df, output_filename)

def group_files_by_number(logs):
    d = { i + 1: [] for i in range(8) }
    for log in logs:
        tag = log.get_experiment_tag()
        num_clients = int(tag.split('-')[1])
        d[num_clients].append(log)
    return d

def lookup(filename, key):
    without_ext = os.path.splitext(filename)[0]
    for kv in without_ext.split('--'):
        pair = kv.split(':')
        if len(pair) == 2 and pair[0] == key:
            return pair[1]
    return ''

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Graph the sender's trace dumped by PCC client")
    parser.add_argument('--dir', '-d', help='directory containing log files', required=True)
    parser.add_argument('--out', '-o', help='directory to dump output files', default='./testing_logs')
    args = parser.parse_args()
    files = [os.path.join(args.dir, f) for f in os.listdir(args.dir)
             if lookup(f,'expt').startswith('intrafairness-') and lookup(f,'host') == 'client']
    print('Opening the following files: %s' % files)

    data = [FileData(f) for f in files]
    # experiments = group_files_by_number(intrafairness_data)
    process(data, args.out)
