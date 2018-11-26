# NetworkSimulator
For CS 143

Output all events enqueued or dequeued along with their time stamps and relevant values at the time to an external file, which the visualizations later draw from. Easier to do than real-time visualizations.

## Plotting
Log events that change relevant statistics. Specifically, per-host send/receive rate, per-link buffer occupancy, packet loss, and flow rate, and per-flow send/receive rate and packet round-trip delay. To plot, run some event manager like `python test.py` and run `python plot.py` which takes the most recent log file output and displays plots for the above.
