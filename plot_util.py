def calc_rate(amounts, nsamples=100):
    """
    Calculate rates as amount/sec. amounts is a list of (time, amount) pairs.
    Return x, y, avg.
    - y[i] is the rate at time x[i]
    - avg is the global average rate
    """
    if not amounts:
        return [], [], 0

    max_time = amounts[-1][0]
    delta = max_time / nsamples

    i = 0  # Current sample index
    total = 0
    x = []
    y = []
    for time, amount in amounts:
        if time > i * delta:
            # Compute rate and shift to new sample
            x.append(i*delta)
            y.append(total/delta)
            total = 0
            i += 1
        total += amount

    return x, y, sum(y) / nsamples

def calc_totals(amounts):
    """
    Calculate cumulative sum.
    Amounts is a list of (t, amount).
    Return x, y, where y[i] is the total at x[i].
    """
    x, y = [], []
    total = 0
    for time, size in amounts:
        x.append(time)
        total += float(size)
        y.append(float(total))
    return x, y
