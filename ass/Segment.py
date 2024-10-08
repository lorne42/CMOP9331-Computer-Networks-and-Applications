import random
import struct

# Define constants for segment types
DATA = 0
ACK = 1
SYN = 2
FIN = 3
MSS = 1000

def create_segment(segment_type, seqno, data=b''):
    # Pack the type and sequence number fields into network byte order (big-endian)
    header = struct.pack('>HH', segment_type, seqno)

    # If it's a data segment, append data
    if segment_type == DATA:
        segment = header + data
    else:
        segment = header

    return segment

def calculate_next_seqno(segment_type, current_seqno, data_size=0):
    if segment_type == DATA:
        return (current_seqno + data_size) % 65535
    elif segment_type == ACK or segment_type == SYN:
        return (current_seqno + 1) % 65535
    elif segment_type == FIN:
        return (current_seqno + 1) % 65535
    else:
        raise ValueError("Invalid segment type")

def parse_segment(segment):
    # Unpack the header of the segment
    segment_type, seqno = struct.unpack('>HH', segment[:4])
    data = segment[4:]  # Extract data from the segment (if present)
    return segment_type, seqno, data

def split_data_into_segments(data):
    segments = []
    for i in range(0, len(data), MSS):
        segment_data = data[i:i + MSS]
        segments.append(segment_data)
    return segments

def mss_loss(prob):
    random_prob = random.random()
    if random_prob >= prob:
        return True
    else:
        return False
