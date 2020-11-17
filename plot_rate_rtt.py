from parse.filedata import FileData

import matplotlib.pyplot as plt
import matplotlib.backends.backend_pdf as pdf

import argparse
import os

def group_data_by_tag(logs):
    'Returns a dictionary of data organized by key.'

    d = dict()
    for log in logs:
        tag = log.get_experiment_tag()
        if tag in d:
            d[tag].append(log)
        else:
            d[tag] = [log]
    return d

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
            names.append(log.get_method())
            contents.plot(x='time', y=key, ax=ax, legend=True)
            print('%s: %s[%s]:' % (log.get_filename(), log.get_method(), key))
            print(contents[key])

    if log_scale:
        ax.set_yscale('log')

    ax.legend(names, loc='lower right')
    out_file.savefig(fig)

def plot_setup(expt_tag, logs, out_dir):

    print('files in this group: ')
    for log in logs:
        print(log.get_filename())

    output_filename = os.path.join(out_dir, '%s.pdf' % expt_tag)
    print('Writing to %s' % output_filename)

    output = pdf.PdfPages(output_filename)
    plot_against_time(logs, 'rate', output, label='Throughput (Mbits/s)')
    plot_against_time(logs, 'rtt', output, label='Latency (ms)')
    plot_against_time(logs, 'rtt', output, label='Latency (ms)', log_scale=True)
    output.close()

def process(log_groups, out_dir, tag=None):
    for expt_tag, logs in log_groups.items():
        if tag is not None and expt_tag == tag or tag is None:
            plot_setup(expt_tag, logs, out_dir)
        else:
            print('Skipping %s' % expt_tag)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Graph the sender's trace dumped by PCC client")
    parser.add_argument('--title', help='title of file')
    parser.add_argument('--dir', '-d', help='directory containing log files', default=None)
    parser.add_argument('--file', '-f', help='log files to plot (overrides -d)', action='append', default=[])
    parser.add_argument('--out', '-o', help='directory to dump output files', default='./testing_logs')
    parser.add_argument('--tag', '-tag', help='tag of experiment to plot', default=None)
    args = parser.parse_args()

    if args.file == [] and args.dir is not None:
        files = [os.path.join(args.dir, f) for f in os.listdir(args.dir) if f.endswith('.txt')]
    else:
        files = args.file

    print('Opening the following files: %s' % files)
    all_file_data = [FileData(f) for f in files]
    experiments = group_data_by_tag(all_file_data)
    process(experiments, args.out, args.tag)
