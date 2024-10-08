import Segment

class Window:
    def __init__(self, max_size):
        self.base = 0  # Base sequence number
        self.next_seqno = 0  # Next sequence number to be sent
        self.max_size = max_size  # Window size
        self.buffer = {}  # Cache of segments sent but not yet acknowledged

    def send_segment(self, segment):
        self.next_seqno = Segment.calculate_next_seqno(Segment.DATA, self.next_seqno, len(segment) - 4)
        self.buffer[self.next_seqno] = segment

    def send_ack_segment(self, seqno, ack_segment):
        self.buffer[seqno] = ack_segment

    def is_empty(self):
        return not self.buffer
