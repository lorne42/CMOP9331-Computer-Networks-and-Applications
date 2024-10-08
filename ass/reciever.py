import math
import os
import socket
import sys
import time
import Segment
import Window

def update_log(text):
    filename = "receiver_log.txt"

    # Check if the file exists
    if not os.path.exists(filename):
        # If the file does not exist, create the file
        with open(filename, "w") as file:
            file.write(text)
    else:
        # If the file exists, append the content
        with open(filename, "a") as file:
            file.write("\n" + text)
    print(text)

if __name__ == "__main__":
    args = sys.argv
    receiver_port = int(args[1])
    sender_port = int(args[2])
    txt_file_to_received = args[3]
    max_win = int(args[4])
    ip = '127.0.0.1'
    udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    udp_socket.bind(("", receiver_port))
    window = Window.Window(max_win)
    received_data = b''
    start_time = time.time()
    dup_data_segments_received = 0
    dup_ack_segments_sent = 0

    while True:
        segment, _ = udp_socket.recvfrom(1024)
        segment_type, seqno, data = Segment.parse_segment(segment)
        if segment_type == Segment.SYN:
            update_log(f"rcv  {(time.time() - start_time):.2f}    SYN {seqno} 0")
            syn_ack_seqno = Segment.calculate_next_seqno(segment_type, seqno)
            syn_ack_segment = Segment.create_segment(Segment.ACK, syn_ack_seqno)
            udp_socket.sendto(syn_ack_segment, (ip, sender_port))
            update_log(f"snd  {(time.time()-start_time):.2f}    ACK {syn_ack_seqno} 0")
            window.base = syn_ack_seqno
            window.next_seqno = syn_ack_seqno
        elif segment_type == Segment.DATA:
            if seqno == window.base:
                # Send ACK
                update_log(f"rcv  {(time.time() - start_time):.2f}    DATA {seqno} {len(data)}")
                ack_seqno = Segment.calculate_next_seqno(segment_type, window.base, len(data))
                ack_segment = Segment.create_segment(Segment.ACK, ack_seqno)
                udp_socket.sendto(ack_segment, (ip, sender_port))
                update_log(f"snd  {(time.time() - start_time):.2f}    ACK {ack_seqno} 0")
                # Update expected sequence number and received data
                window.base = ack_seqno
                received_data += data
                while window.base in window.buffer:
                    del window.buffer[window.base]
                    ack_seqno = Segment.calculate_next_seqno(segment_type, window.base, len(data))
                    window.base = ack_seqno
                    received_data += data
            elif seqno < window.base:
                dup_data_segments_received += 1
                update_log(f"rcv  {(time.time() - start_time):.2f}    DATA {seqno} {len(data)}")
                ack_seqno = Segment.calculate_next_seqno(segment_type, seqno, len(data))
                ack_segment = Segment.create_segment(Segment.ACK, ack_seqno)
                udp_socket.sendto(ack_segment, (ip, sender_port))
                update_log(f"snd  {(time.time() - start_time):.2f}    ACK {ack_seqno} 0")
                dup_ack_segments_sent += 1
            elif seqno > window.base and seqno < window.base + max_win:
                window.buffer[seqno] = segment
                # Send ACK
                update_log(f"rcv  {(time.time() - start_time):.2f}    DATA {seqno} {len(data)}")
                ack_seqno = Segment.calculate_next_seqno(segment_type, seqno, len(data))
                ack_segment = Segment.create_segment(Segment.ACK, ack_seqno)
                udp_socket.sendto(ack_segment, (ip, sender_port))
                update_log(f"snd  {(time.time() - start_time):.2f}    ACK {ack_seqno} 0")
        elif segment_type == Segment.FIN:
            # Send FIN_ACK
            update_log(f"rcv  {(time.time() - start_time):.2f}    FIN {seqno} 0")
            ack_segment = Segment.create_segment(Segment.ACK, seqno + 1)
            udp_socket.sendto(ack_segment, (ip, sender_port))
            update_log(f"snd  {(time.time() - start_time):.2f}    ACK {seqno+1} 0")
            print(f"Received FIN segment with seqno: {seqno}. Sent FIN_ACK: {seqno + 1}")
            # End receiving
            break
        else:
            # Invalid segment, ignore
            print(f"Received invalid segment with seqno: {seqno}. Discarding...")

    # Print received data
    with open(txt_file_to_received, "wb") as file:
        file.write(received_data)
    original_data_received = len(received_data)
    original_segments_received = math.ceil(len(received_data)/Segment.MSS)
    update_log(f"Original data received: {original_data_received}\n"
               f"Original segments received: {original_segments_received}\n"
               f"Dup data segments received: {dup_data_segments_received}\n"
               f"Dup ack segments sent: {dup_ack_segments_sent} ")
    # Close socket
    time.sleep(2)
    udp_socket.close()
