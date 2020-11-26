from parse.filedata import FileData

import matplotlib.pyplot as plt
import matplotlib.backends.backend_pdf as pdf
import pandas as pd

import argparse
import os

warning_color = '\033[93m'
end_color = '\033[0m'

def print_warning(s):
    print(warning_color + 'WARNING: %s' % s + end_color)

def plot_against_time(logs, key, out_file, label=None, log_scale=False):
    if label is None:
        label = key
    fig, ax = plt.subplots()
    ax.set_xlabel('Time (ms)')
    ax.set_ylabel('%s' % key)
    ax.set_title('%s against time' % label)

    names = []
    for log in logs:
        contents = log.get_contents()
        if 'time' in contents and key in contents:
            names.append(log.get_label())
            contents.plot(x='time', y=key, ax=ax, legend=True)
            print('%s: %s[%s] ok' % (log.get_filename(), log.get_label(), key))
            # print('%s: %s[%s]:' % (log.get_filename(), log.get_label(), key))
            # print(contents[key])
        else:
            print_warning('Cannot plot %s: time or key = %s is not in table' % (log.get_filename(), key))

    if log_scale:
        ax.set_yscale('log')

    ax.legend(names, loc='lower right')
    out_file.savefig(fig)

def print_filenames(logs):
    print('files in this group: ')
    for log in logs:
        print(log.get_filename())

def label_for_x(variable):
    if variable == 'bw':
        return 'Bandwidth'
    elif variable == 'delay':
        return 'Latency'
    elif variable == 'loss':
        return 'Loss rate'
    elif variable == 'queue':
        return 'Buffer size'
    else:
        raise ValueError()

def label_for_y(y):
    if y == 'util':
        return 'Link Utilization'
    elif y == 'rtt':
        return 'Self-inflicted Latency'
    else:
        raise ValueError()

def plot(x, y, data, outfile):
    fig, ax = plt.subplots()
    ax.set_xlabel('%s' % label_for_x(x))
    ax.set_ylabel(label_for_y(y))
    ax.set_title('%s sensitivity' % label_for_x(x))

    method_data = data.groupby('method')
    names = []

    for method_name, group in method_data:
        names.append(method_name)
        # ylim = (0, 1.5) if y == 'util' else None
        ylim = None
        group.sort_values(x).plot(x=x, y=y, ax=ax, marker='x', ylim=ylim)
    ax.legend(names, loc='lower right')
    outfile.savefig(fig)

def process_setup(variable, logs, outfile):
    # Currently kept in sync with Mininet script manually, but should be exported to filename...
    network_bw = 30

    rows = []
    for log in logs:
        contents = log.get_contents()
        try:
            tag = log.get_experiment_tag()
            param = get_expt_param(tag)
            throughput = contents['rate'].quantile(0.5) # mean is too sensitive to outliers
            utilization = throughput / (int(param) if variable == 'bw' else network_bw)
            mean_rtt = contents['rtt'].mean()
            rows.append({'method': log.get_meta('method'), variable: int(param), 'util': utilization, 'rtt': mean_rtt})
        except KeyError:
            print_warning('%s is corrupted' % log.get_filename())
    data = pd.DataFrame(rows)
    plot(variable, 'util', data, outfile)
    plot(variable, 'rtt', data, outfile)

def process(log_groups, out_dir):
    output_filename = os.path.join(out_dir, 'figure6.pdf')
    print('Writing to %s' % output_filename)
    output = pdf.PdfPages(output_filename)

    for expt_typ, logs in log_groups.items():
        process_setup(expt_typ, logs, output)

    output.close()

def lookup(filename, key):
    without_ext = os.path.splitext(filename)[0]
    for kv in without_ext.split('--'):
        pair = kv.split(':')
        if len(pair) == 2 and pair[0] == key:
            return pair[1]
    return ''

def get_expt_type(tag):
    return tag.split('-')[1]

def get_expt_param(tag):
    [_, _variable, param] = tag.split('-')
    return param

def group_files_by_type(logs):
    d = {'bw': [], 'delay': [], 'loss': [], 'queue': []}
    for log in logs:
        tag = log.get_experiment_tag()
        typ = get_expt_type(tag)
        if typ == 'single':
            continue # ignore single runs
        d[typ].append(log)
    return d

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Graph the sender's trace dumped by PCC client")
    parser.add_argument('--dir', '-d', help='directory containing log files', required=True)
    parser.add_argument('--out', '-o', help='directory to dump output files', default='./testing_logs')
    args = parser.parse_args()
    files = [os.path.join(args.dir, f) for f in os.listdir(args.dir)
             if lookup(f,'expt').startswith('figure6-') and lookup(f,'host') == 'client']
    print('Opening the following files: %s' % files)

    figure6_data = [FileData(f) for f in files]
    experiments = group_files_by_type(figure6_data)
    process(experiments, args.out)
