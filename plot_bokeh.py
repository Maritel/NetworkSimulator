from bokeh.layouts import column
from bokeh.plotting import figure, gridplot, output_file, save
from bokeh.models import Span
import os
from pathlib import Path
from plot_util import calc_rate, calc_totals
import sys

def load_data(file_name):
    data = {}
    with open(file_name) as f:
        for line in f:
            if '|' in line:
                part = line.split('|')
                if part[0] not in data:
                    data[part[0]] = {}
                if part[1] not in data[part[0]]:
                    data[part[0]][part[1]] = {}
                if part[4] not in data[part[0]][part[1]]:
                    data[part[0]][part[1]][part[4]] = []
                # Record time step for appropriate and specific component
                data[part[0]][part[1]][part[4]].append((float(part[3]), float(part[5])))
    return data


def main():
    if(len(sys.argv) == 1):
        file_names = [f for f in os.listdir('.') if os.path.isfile(f) and f.startswith('log_') and f.endswith('.txt')]
        if not file_names:
            raise ValueError('No log files')
        # Get most recent file name
        file_name = max(file_names)
    else:
        file_name = Path(sys.argv[1])

    plotfile = os.path.splitext(file_name)[0] + '_plots.html'
    output_file(plotfile)

    data = load_data(file_name)

    host_data = data['HOST']
    grid = []
    for host in host_data:
        host_send_data = host_data[host]['SEND']
        host_rcve_data = host_data[host]['RCVE']

        f = figure(
            title='{}: Send and receive rate vs. time'.format(host),
            x_axis_label='Time (s)',
            y_axis_label='Rate (bits/s)'
        )
        x, y, _ = calc_rate(host_send_data)
        f.line(x, y, legend='Send', line_color='blue')
        x, y, _ = calc_rate(host_rcve_data)
        f.line(x, y, legend='Receive', line_color='red')
        grid.append([f])
    host_grid = gridplot(grid, plot_width=900, plot_height=300)


    link_data = data['LINK']
    grid = []
    for link in sorted(data['LINK']):
        link_buff_data = link_data[link]['BUFF']
        link_loss_data = link_data[link].get('LOSS', [])
        link_flow_data = link_data[link]['FLOW']
        link_figs = []

        ### Per-link buffer occupancy ###
        f = figure(
            title='{}: Link buffer'.format(link),
            x_axis_label='Time (s)',
            y_axis_label='Buffer size (bits)'
        )
        x, y = calc_totals(link_buff_data)
        # Use mode=after, because y[i] is the buffer size at time x[i] and
        # thereafter
        f.step(x, y, mode='after')
        link_figs.append(f)

        ### Per-link packet loss ###
        f = figure(
            title='{}: Link packet loss'.format(link),
            x_axis_label='Time (s)',
            y_axis_label='Loss rate (#pkts/s)'
        )
        x, y, avg = calc_rate(link_loss_data)
        f.line(x, y)
        link_figs.append(f)

        ### Per-link flow rate ###
        f = figure(
            title='{}: Link flow rate'.format(link),
            x_axis_label='Time (s)',
            y_axis_label='Flow rate (b/s)'
        )
        x, y, avg = calc_rate(link_flow_data)
        f.line(x, y)
        link_figs.append(f)

        grid.append(link_figs)
    link_grid = gridplot(grid, plot_width=500, plot_height=200)
    

    flow_data = data['FLOW']
    grid = []
    for flow in sorted(flow_data):
        flow_figs = []
        ### Per-flow send rate ###
        f = figure(
            title='{}: Send and receive rate'.format(flow),
            x_axis_label='Time (s)',
            y_axis_label='Send rate (bits/s)'
        )
        flow_send_data = flow_data[flow].get('SEND', [])
        x, y, avg = calc_rate(flow_send_data)
        f.line(x, y, color='blue', legend='Send')
        flow_rcve_data = flow_data[flow].get('RCVE', [])
        x, y, avg = calc_rate(flow_rcve_data)
        f.line(x, y, color='red', legend='Receive')
        flow_tput_data = flow_data[flow].get('THROUGHPUT', [])
        x, y, avg = calc_rate(flow_tput_data)
        f.line(x, y, color='green', legend='Throughput')
        flow_figs.append(f)

        ### Per-flow window size ###
        f = figure(
            title='{}: Window size (vertical dashes are ack timeouts)'.format(flow),
            x_axis_label='Time (s)',
            y_axis_label='Window size (#pkts)'
        )
        flow_window_data = flow_data[flow]['WINDOW']
        x, y = zip(*flow_window_data)
        f.step(x, y, color='blue', mode='after', legend='Window')
        if 'SSTHRESH' in flow_data[flow]:
            x, y = zip(*flow_data[flow]['SSTHRESH'])
            f.step(x, y, color='red', mode='after', legend='ssthresh')
        flow_ack_timeout_data = flow_data[flow].get('ACKTIMEOUT', [])
        for t, _ in flow_ack_timeout_data:
            f.add_layout(Span(location=t, dimension='height', line_color='black', line_dash='dashed'))
        f.legend.click_policy="hide"
        flow_figs.append(f)

        f = figure(
            title='{}: Ack rates'.format(flow),
            x_axis_label='Time (s)',
            y_axis_label='Ack rates (#/s)'
        )
        x, y, avg = calc_rate(flow_data[flow].get('POSACK', []))
        f.line(x, y, color='green', legend='Posacks')
        x, y, avg = calc_rate(flow_data[flow].get('DUPACK', []))
        f.line(x, y, color='red', legend='Dupacks')
        flow_figs.append(f)

        ### Per-flow round trip delay ###
        flow_rtt_data = flow_data[flow].get('RTT', [])
        f = figure(
            title='{}: RTT'.format(flow),
            x_axis_label='Time (s)',
            y_axis_label='RTT (s)'
        )
        x, y = zip(*flow_rtt_data)  # transpose
        f.step(x, y, mode='after')
        flow_figs.append(f)

        grid.append(flow_figs)
    flow_grid = gridplot(grid, plot_width=700, plot_height=400)

    p = column(host_grid, link_grid, flow_grid)
    save(p)

    print('Wrote plots to', plotfile)

main()