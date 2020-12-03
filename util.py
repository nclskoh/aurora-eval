warning_color = '\033[93m'
end_color = '\033[0m'

def print_warning(s):
    print(warning_color + 'WARNING: %s' % s + end_color)

def legend_name(label):
    if label.find('cubic') >= 0:
        return 'cubic'
    elif label.find('aurora') >= 0:
        return 'aurora'
    elif label.find('vivace') >= 0:
        return 'vivace'
    else:
        raise ValueError('Unknown label: %s' % label)

colors = ['#1f77b4', # default blue
          '#ff7f0e', # default orange
          '#2ca02c', # default green
          '#d62728',
          '#9467bd',
          '#8c564b',
          '#e377c2',
          '#7f7f7f',
          '#bcbd22',
          '#17becf']

def color(label, existing):
    'Assign color following ICML paper if possible, but pick another color '
    'if the method has already appeared'
    'Assume label to be cubic/aurora/vivace'

    if label not in existing:
        if label.find('cubic') >= 0:
            return colors[0]
        elif label.find('aurora') >= 0:
            return colors[1]
        elif label.find('vivace') >= 0:
            return colors[2]
    else:
        if label.find('cubic') >= 0:
            return colors[3]
        elif label.find('aurora') >= 0:
            return colors[4]
        elif label.find('vivace') >= 0:
            return colors[9]
    raise ValueError('Unknown label: %s' % label)
