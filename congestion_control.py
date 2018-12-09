from abc import ABC, abstractmethod

class CongestionControl(ABC):
    """Congestion control determines the window size (cwnd) during a TCP
    connection."""

    @abstractmethod
    def initial_cwnd(self):
        """Return the initial cwnd"""
        pass
    
    @abstractmethod
    def posack(self):
        """Called on a posACK. Return new value of cwnd."""
        pass
    
    @abstractmethod
    def dupack(self):
        """Called on a dupACK (ack number == sequence number of first
        unacknowledged packet). Return (retransmit, cwnd), where retransmit
        is whether to start retransmitting from the unacknowledged packet,
        and cwnd is the new cwnd."""
        pass
    
    @abstractmethod
    def ack_timeout(self):
        """Called on an ACK timeout. Return new cwnd."""
        pass

class StopAndWait(CongestionControl):
    """The simplest congestion control. Basically a window size of 1."""
    def initial_cwnd(self):
        return 1
    
    def posack(self):
        return 1
    
    def dupack(self):
        # Even though the window size is 1, dupACKs are still possible
        # (edge cases)
        return False, 1
    
    def ack_timeout(self):
        return 1


class Reno(CongestionControl):
    # https://www.ietf.org/rfc/rfc2581.txt
    
    def __init__(self, debug=True):
        self.cwnd = 1
        self.ssthresh = float('inf')
        self.n_dupacks = 0          # Number of dupacks in a row
        self.fast_recovery = False  # Whether we're in fast recovery mode
    
    def initial_cwnd(self):
        return 1

    def get_int_cwnd(self):
        return 1 if self.cwnd < 1 else int(round(self.cwnd))

    def posack(self):
        self.n_dupacks = 0

        if self.fast_recovery: # Exit FR/FR and deflate window
            self.fast_recovery = False
            self.cwnd = self.ssthresh
        
        if self.cwnd < self.ssthresh: # Slow start; window *= 2 each RTT
            self.cwnd += 1
        else: # Congestion avoidance; attempt window += 1 every RTT
            self.cwnd += 1 / self.cwnd
        
        return self.get_int_cwnd()
    
    def dupack(self):
        self.n_dupacks += 1

        if not self.fast_recovery and self.n_dupacks == 3: # Enter FR/FR
            self.fast_recovery = True
            self.ssthresh = max(self.cwnd // 2, 2)
            self.cwnd = self.ssthresh + 3
            return True, self.cwnd
        
        if self.fast_recovery:
            # For each additional dupack, inflate window
            self.cwnd += 1
        
        return False, self.get_int_cwnd()
    
    def ack_timeout(self):
        self.n_dupacks = 0
        self.fast_recovery = False

        self.ssthresh = max(self.cwnd // 2, 2)
        self.cwnd = 1
        return self.get_int_cwnd()
        


