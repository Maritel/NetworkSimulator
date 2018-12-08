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
    
    def posack(self):
        self.n_dupacks = 0

        if self.cwnd < self.ssthresh: # Slow start
            assert not self.fast_recovery
            self.cwnd += 1
        else:
            if self.fast_recovery: # Exit FR/FR and deflate window
                self.fast_recovery = False
                self.cwnd = self.ssthresh
            
            # Congestion avoidance
            self.cwnd += 1/self.cwnd
        
        return int(self.cwnd)
    
    def dupack(self):
        # If slow start, do nothing
        if self.cwnd >= self.ssthresh:
            if self.fast_recovery:  # FR/FR
                # For each additional dupack, inflate window
                self.cwnd += 1
            else:  # CA
                self.n_dupacks += 1
                if self.n_dupacks == 3: # Enter FR/FR
                    self.fast_recovery = True
                    self.ssthresh = max(self.cwnd // 2, 2)
                    self.cwnd = self.ssthresh + 3
                    return True, self.cwnd        
        return False, self.cwnd
    
    def ack_timeout(self):
        # If in FR/FR, always exit
        # Same behavior for SS and CA
        self.n_dupacks = 0
        self.fast_recovery = False
        self.ssthresh = max(self.cwnd // 2, 2)
        self.cwnd = 1
        return self.cwnd
        


