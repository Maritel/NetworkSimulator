import matplotlib.pyplot as plt
import os

# TODO: Verify correctness by matching to time traces for Test Case 1
# sub TODO: Make sure that flow send/receive rates are computed correctly. Figure out flow ends vs. flow???
# sub TODO: Make sure that host send/receive rates and link flow rates don't need to be computed with some window size?
# TODO: Refactor code to be more modular and allow for plotting of specific statistics.

if __name__ == '__main__':
    file_names = [f for f in os.listdir('.') if os.path.isfile(f) and 'log' in f]

    # Get most recent file name
    file_name = ''
    for fn in file_names:
        if file_name == '' or fn > file_name:
            file_name = fn

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
                data[part[0]][part[1]][part[4]].append((part[3], part[5]))

    # Handle host plotting
    host_data = data['HOST']
    plt.figure()
    rows = len(host_data)
    cols = 2
    index = 1

    for host in host_data:
        host_send_data = host_data[host]['SEND']
        host_rcve_data = host_data[host]['RCVE']

        ### Per-host send rate ###
        x, y = [], []
        for time, size in host_send_data:
            x.append(float(time))
            y.append(float(size))

        plt.subplot(rows, cols, index)
        index += 1
        plt.plot(x, y)
        plt.xlabel('Time (s)')
        plt.ylabel('Send rate (bits/s)')
        plt.title('{}: Send rate vs. time'.format(host))

        print('Average send rate for host {}: {}'.format(host, sum(y)/x[-1]))

        ### Per-host receive rate ###
        x, y = [], []
        total = 0
        for time, size in host_rcve_data:
            x.append(float(time))
            y.append(float(size))

        plt.subplot(rows, cols, index)
        index += 1
        plt.plot(x, y)
        plt.xlabel('Time (s)')
        plt.ylabel('Receive rate (bits/s)')
        plt.title('{}: Receive rate vs. time'.format(host))

        print('Average receive rate for host {}: {}'.format(host, sum(y)/len(y)))

    plt.tight_layout()
    plt.show()

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

        plt.figure()
        # plt.subplot(rows, cols, index)
        index += 1
        plt.plot(x, y)
        plt.xlabel('Time (s)')
        plt.ylabel('Link buffer (b)')
        plt.title('{}: Link buffer vs. time'.format(link))
        plt.show()

        print('Average buffer occupancy for link {}: {}'.format(link, sum(y)/len(y)))

        ### Per-link packet loss ###
        x, y = [], []
        total = 0
        for time, pkt in link_loss_data:
            x.append(float(time))
            y.append(int(pkt))

        plt.figure()
        index += 1
        plt.plot(x, y)
        plt.xlabel('Time (s)')
        plt.ylabel('Packet loss (#pkts)')
        plt.title('{}: Lost packets vs. time'.format(link))
        plt.show()

        if y:
            print('Average lost packets for link {}: {}'.format(link, y[-1]/len(y)))

        ### Per-link flow rate ###
        x, y = [], []
        total = 0
        for time, size in link_flow_data:
            x.append(float(time))
            y.append(float(size))

        # plt.subplot(rows, cols, index)
        plt.figure()
        # index += 1
        plt.plot(x, y)
        plt.xlabel('Time (s)')
        plt.ylabel('Link flow rate (b/s)')
        plt.title('{}: Link flow rate vs. time'.format(link))
        plt.show()

        print('Average flow rate for link {}: {}'.format(link, sum(y)/len(y)))

    plt.tight_layout()
    plt.show()

    # Handle flow plotting
    flow_data = data['FLOW']
    plt.figure()
    rows = len(flow_data)
    cols = 3
    index = 1

    for flow in flow_data:
        ### Per-flow send rate ###
        if 'SEND' in flow_data[flow]:
            flow_send_data = flow_data[flow]['SEND']
            x, y = [], []
            total = 0
            for time, size in flow_send_data:
                x.append(float(time))
                y.append(float(size))

            plt.subplot(rows, cols, index)
            index += 1
            plt.plot(x, y)
            plt.xlabel('Time (s)')
            plt.ylabel('Send rate (bits/s)')
            plt.title('{}: Send rate vs. time'.format(flow))

            print('Average send rate for link {}: {}'.format(link, sum(y)/len(y)))


        ### Per-flow receive rate ###
        if 'RCVE' in flow_data[flow]:
            flow_rcve_data = flow_data[flow]['RCVE']
            x, y = [], []
            total = 0
            for time, size in flow_rcve_data:
                x.append(float(time))
                y.append(float(size))

            plt.subplot(rows, cols, index)
            index += 1
            plt.plot(x, y)
            plt.xlabel('Time (s)')
            plt.ylabel('Receive rate (bits/s)')
            plt.title('{}: Receive rate vs. time'.format(flow))

            print('Average receive rate for link {}: {}'.format(link, sum(y)/len(y)))


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

            print('Average RTT for flow {}: {}'.format(flow, sum(y)/len(y)))

    plt.tight_layout()
    plt.show()

