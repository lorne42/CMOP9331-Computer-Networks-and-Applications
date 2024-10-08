import socket
import random
import sys
import Window
import clock
import Segment


def generate_random_seqno():
    return random.randint(0, 65535)


def segment_datas_no(seqno, syn_ack, i):
    if seqno < syn_ack:
        i += 1
        a = (seqno + i * 65535 - syn_ack) // Segment.MSS
        if (seqno - syn_ack) % Segment.MSS != 0:
            b = 1
        else:
            b = 0
    else:
        a = (seqno - syn_ack) // Segment.MSS
        if (seqno - syn_ack) % Segment.MSS != 0:
            b = 1
        else:
            b = 0
    return a + b, i


if __name__ == "__main__":
    args = sys.argv
    sender_port = int(args[1])
    receiver_port = int(args[2])
    Txt_file_to_send = args[3]
    Max_win = int(args[4])
    rto = int(args[5])
    flp = float(args[6])
    rlp = float(args[7])

    Original_segments_sent = 0
    Retransmitted_segments = 0
    Dup_acks_received = 0
    Data_segments_dropped = 0
    Ack_segments_dropped = 0

    ip = '127.0.0.1'
    udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    udp_socket.bind(("", sender_port))
    udp_socket.settimeout(5)
    ISN = generate_random_seqno()
    syn_seqno = ISN
    syn_segment = Segment.create_segment(Segment.SYN, syn_seqno)

    if Segment.mss_loss(flp):
        udp_socket.sendto(syn_segment, (ip, receiver_port))
        print("SYN sent")
    else:
        print("SYN sending failed")

    timeout_seconds = rto / 1000
    timer1 = clock.Timer(timeout_seconds)
    timer1.start()

    while True:
        if timer1.check_timeout():
            Retransmitted_segments += 1
            if Segment.mss_loss(flp):
                udp_socket.sendto(syn_segment, (ip, receiver_port))
                print("SYN sent")
                break
            else:
                print("SYN sending failed")
            timer1.reset()

        try:
            if Segment.mss_loss(rlp):
                # Wait to receive SYN-ACK
                syn_ack_segment, _ = udp_socket.recvfrom(1024)
                segment_type, ack_seqno, _ = Segment.parse_segment(syn_ack_segment)
                if segment_type == Segment.ACK:
                    print("Received SYN-ACK")
                    timer1.stop()
                    break
                else:
                    print("Received unexpected segment")
            else:
                Ack_segments_dropped += 1
        except socket.timeout:
            print("Waiting")

    dupACKcount = 0
    window = Window.Window(Max_win)
    syn_ack_no = syn_seqno + 1
    window.base = syn_ack_no
    window.next_seqno = syn_ack_no
    segment_datas = []
    timer2 = clock.Timer(timeout_seconds)

    with open(Txt_file_to_send, 'rb') as file:
        file_data = file.read()
        Original_data_sent = len(file_data)
        Original_data_acked = len(file_data)

    # Split the file data into multiple data segments
    segment_datas = Segment.split_data_into_segments(file_data)
    Original_segments_sent = len(segment_datas)
    current_seqno = syn_ack_no

    # Set sequence numbers for each segment
    for i in range(len(segment_datas)):
        segment_datas[i] = Segment.create_segment(Segment.DATA, current_seqno, segment_datas[i])
        current_seqno = Segment.calculate_next_seqno(Segment.DATA, current_seqno, len(segment_datas[i]) - 4)

    i = 0
    while window.base - syn_ack_no < len(file_data):

        # Send data within the window
        while window.next_seqno < window.base + Max_win and window.next_seqno < len(file_data) + syn_ack_no:
            no, i = segment_datas_no(window.next_seqno, syn_ack_no, i)
            if no < len(segment_datas):
                if Segment.mss_loss(flp):
                    udp_socket.sendto(segment_datas[no], (ip, receiver_port))
                    print(f"Sending: {window.next_seqno}")
                else:
                    Data_segments_dropped += 1
                window.send_segment(segment_datas[no])
                if not timer2.is_running:
                    timer2 = clock.Timer(timeout_seconds)
                    timer2.start()

        # Timeout retransmission
        if timer2.check_timeout():
            if Segment.mss_loss(flp):
                udp_socket.sendto(window.buffer[next(iter(window.buffer))], (ip, receiver_port))
                print(f"reSending: {next(iter(window.buffer))}")
            else:
                Data_segments_dropped += 1
            Retransmitted_segments += 1
            timer2.reset()
            dupACKcount = 0

        # Receive ack events
        try:
            ack, address = udp_socket.recvfrom(1024)
            segment_type, ack_num, _ = Segment.parse_segment(ack)
            if Segment.mss_loss(rlp):
                # Update base pointer
                if segment_type == Segment.ACK:
                    if ack_num in window.buffer:
                        del window.buffer[ack_num]
                        if not window.is_empty():
                            earliest_ackno = next(iter(window.buffer))
                            _, earlistseq, _ = Segment.parse_segment(window.buffer[earliest_ackno])
                            window.base = earlistseq
                        else:
                            window.base = window.next_seqno
                        print(f"Received ACK: {ack_num}")
                        if window.is_empty():
                            timer2.stop()
                        else:
                            timer2.reset()
                        dupACKcount = 0
                    else:
                        dupACKcount += 1
                        Dup_acks_received += 1
                        if dupACKcount == 3:
                            Retransmitted_segments += 1
                            if Segment.mss_loss(flp):
                                udp_socket.sendto(window.buffer[next(iter(window.buffer))], (ip, receiver_port))
                                print(f"reSending: {window.buffer[0]}")
                                break
                            else:
                                Data_segments_dropped += 1
                else:
                    print(f"Received invalid ACK: {ack_num}")
            else:
                Ack_segments_dropped += 1
        except socket.timeout:
            print('Waiting for ack')

    segment = Segment.create_segment(Segment.FIN, window.base)
    udp_socket.sendto(segment, (ip, receiver_port))
    print(f"Sending FIN segment with seqno: {window.base}")

    # Wait to receive FIN_ACK
    while True:
        try:
            udp_socket.settimeout(rto)
            fin_ack, address = udp_socket.recvfrom(1024)
            segment_type, ack_num, _ = Segment.parse_segment(fin_ack)

            if segment_type == Segment.ACK and ack_num == window.base + 1:
                print(f"Received FIN_ACK: {ack_num}")
                break
            else:
                print(f"Received invalid FIN_ACK: {ack_num}")

        except socket.timeout:
            print("Timeout! Did not receive FIN_ACK.")

    filename = "sender_log.txt"
    text = (f"Original_data_sent:{Original_data_sent}\nOriginal_data_acked:{Original_data_acked}\n"
            f"Original_segments_sent:{Original_segments_sent}\nRetransmitted_segments:{Retransmitted_segments}\n"
            f"Dup_acks_received:{Dup_acks_received}\nData_segments_dropped:{Data_segments_dropped}\nAck_segments_dropped:{Ack_segments_dropped}")
    with open(filename, "w") as file:
        file.write(text)

    # Close the socket
    udp_socket.close()
