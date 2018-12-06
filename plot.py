import matplotlib.pyplot as plt
import os
from pathlib import Path
from plot_util import calc_rate
import sys

# TODO: Verify correctness by matching to time traces for Test Case 1
# sub TODO: Make sure that flow send/receive rates are computed correctly. Figure out flow ends vs. flow???
# sub TODO: Make sure that host send/receive rates and link flow rates don't need to be computed with some window size?
# TODO: Refactor code to be more modular and allow for plotting of specific statistics.


SUBPLOT_HEIGHT = 4
SUBPLOT_WIDTH = 8


if __name__ == '__main__':
    if(len(sys.argv) == 1):
        file_names = [f for f in os.listdir('.') if os.path.isfile(f) and f.startswith('log_') and f.endswith('.txt')]

        # Get most recent file name
        file_name = ''
        for fn in file_names:
            if file_name == '' or fn > file_name:
                file_name = fn
    else:
        file_name = Path(sys.argv[1])

    # plotdir = Path(os.path.splitext(file_name)[0] + '_plots')
    plotdir = os.path.splitext(file_name)[0] + '_plots/'
    # plotdir.mkdir(exist_ok=True)
    os.makedirs(plotdir, exist_ok=True)


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

    # Handle host plotting
    host_data = data['HOST']
    rows = len(host_data)
    cols = 2
    index = 1
    plt.close()
    plt.figure(figsize=(SUBPLOT_WIDTH*cols, SUBPLOT_HEIGHT*rows)) # width, height

    for host in host_data:
        host_send_data = host_data[host]['SEND']
        host_rcve_data = host_data[host]['RCVE']

        ### Per-host send rate ###
        plt.subplot(rows, cols, index)
        index += 1
        x, y, avg = calc_rate(host_send_data)
        plt.plot(x, y)
        plt.xlabel('Time (s)')
        plt.ylabel('Send rate (bits/s)')
        plt.title('{}: Send rate vs. time'.format(host))
        print('Average send rate for host {}: {} bits/s'.format(host, avg))

        ### Per-host receive rate ###
        plt.subplot(rows, cols, index)
        index += 1
        x, y, avg = calc_rate(host_rcve_data)
        plt.plot(x, y)
        plt.xlabel('Time (s)')
        plt.ylabel('Receive rate (bits/s)')
        plt.title('{}: Receive rate vs. time'.format(host))
        print('Average receive rate for host {}: {} bits/s'.format(host, avg))

    plt.tight_layout()
    plt.savefig(plotdir + "hosts.png", dpi=200)
    plt.close('all')


    # Handle link plotting
    link_data = data['LINK']
    # plt.figure()
    rows = len(link_data)
    cols = 3
    index = 1

    for link in link_data:
        link_buff_data = link_data[link]['BUFF']
        if 'LOSS' in link_data[link]:
            link_loss_data = link_data[link]['LOSS']
        else:
            link_loss_data = []
        link_flow_data = link_data[link]['FLOW']

        ### Per-link buffer occupancy ###
        x, y = [], []
        total = 0
        for time, size in link_buff_data:
            x.append(float(time))
            total += float(size)
            y.append(float(total))
        plt.close()
        plt.figure(figsize=(10, 4))
        # plt.subplot(rows, cols, index)
        index += 1
        plt.step(x, y, where='post')
        plt.xlabel('Time (s)')
        plt.ylabel('Link buffer (b)')
        plt.title('{}: Link buffer vs. time'.format(link))
        plt.savefig(plotdir + "link_{}_buffer.png".format(link), dpi=200)
        plt.close('all')

        print('Average buffer occupancy for link {}: {} bits'.format(link, sum(y)/len(y)))

        ### Per-link packet loss ###
        plt.close()
        plt.figure(figsize=(10, 4))
        index += 1
        x, y, avg = calc_rate(link_loss_data)
        plt.plot(x, y)
        plt.xlabel('Time (s)')
        plt.ylabel('Loss rate (#pkts/s)')
        plt.title('{}: Lost packets vs. time'.format(link))
        plt.savefig(plotdir + "link_{}_pkt_loss.png".format(link), dpi=200)
        plt.close('all')
        print('Average loss rate for link {}: {} pkts/s'.format(link, avg))

        ### Per-link flow rate ###
        # plt.subplot(rows, cols, index)
        plt.close()
        plt.figure(figsize=(10, 4))
        x, y, avg = calc_rate(link_flow_data)
        # index += 1
        plt.plot(x, y)
        plt.xlabel('Time (s)')
        plt.ylabel('Link flow rate (b/s)')
        plt.title('{}: Link flow rate vs. time'.format(link))
        plt.savefig(plotdir + "link_{}_flow_rate.png".format(link), dpi=200)
        plt.close('all')
        print('Average flow rate for link {}: {} bits/s'.format(link, avg))

    # plt.tight_layout()
    # plt.savefig(str(ctr) + ".png", dpi=200); ctr += 1

    # Handle flow plotting
    flow_data = data['FLOW']
    rows = len(flow_data)
    cols = 4
    index = 1
    plt.close()
    plt.figure(figsize=(SUBPLOT_WIDTH*cols, SUBPLOT_HEIGHT*rows)) # width, height

    for flow in flow_data:
        ### Per-flow send rate ###
        if 'SEND' in flow_data[flow]:
            flow_send_data = flow_data[flow]['SEND']
            plt.subplot(rows, cols, index)
            index += 1
            x, y, avg = calc_rate(flow_send_data)
            plt.plot(x, y)
            plt.xlabel('Time (s)')
            plt.ylabel('Send rate (bits/s)')
            plt.title('{}: Send rate vs. time'.format(flow))
            print('Average send rate for flow {}: {} bits/s'.format(flow, avg))


        ### Per-flow receive rate ###
        if 'RCVE' in flow_data[flow]:
            flow_rcve_data = flow_data[flow]['RCVE']
            plt.subplot(rows, cols, index)
            index += 1
            x, y, avg = calc_rate(flow_rcve_data)
            plt.plot(x, y)
            plt.xlabel('Time (s)')
            plt.ylabel('Receive rate (bits/s)')
            plt.title('{}: Receive rate vs. time'.format(flow))
            print('Average receive rate for flow {}: {} bits/s'.format(flow, avg))


        ### Per-flow window size ###
        if 'WINDOW' in flow_data[flow]:
            flow_window_data = flow_data[flow]['WINDOW']
            x, y = [], []
            total = 0
            for time, size in flow_window_data:
                x.append(float(time))
                y.append(float(size))

            plt.subplot(rows, cols, index)
            index += 1
            plt.step(x, y, where='post')
            plt.xlabel('Time (s)')
            plt.ylabel('Window size (# pkts)')
            plt.title('{}: Window size vs. time'.format(flow))
            print('Average window size for flow {}: {} pkts'.format(flow, sum(y)/len(y)))


        ### Per-flow round trip delay ###
        if 'RTT' in flow_data[flow]:
            flow_rtt_data = flow_data[flow]['RTT']
            x, y = [], []
            total = 0
            for time, delay in flow_rtt_data:
                x.append(float(time))
                y.append(float(delay))

            plt.subplot(rows, cols, index)
            index += 1
            plt.plot(x, y)
            plt.xlabel('Time (s)')
            plt.ylabel('RTT (s)')
            plt.title('{}: RTT vs. time'.format(flow))

            print('Average RTT for flow {}: {}s'.format(flow, sum(y)/len(y)))

    plt.tight_layout()
    plt.savefig(plotdir + "flows.png")
    plt.close('all')

