import socket
import time
import datetime
import random
import sys

def main():
    args = sys.argv
    all_rtt=[]
    ip=args[1]
    port=int(args[2])
    udp_socket=socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    udp_socket.settimeout(0.6)
    n=random.randint(50000, 60000)
    for i in range(20):
        date=datetime.datetime.now()
        try:
            sp=time.time()
            text="PING "+ip+" "+str(n)+" "+date.strftime("%Y-%m-%d %H:%M:%S")
            udp_socket.sendto(text.encode('utf-8'), (ip, port))
            recieve_msg=udp_socket.recvfrom(2048)
            fp=time.time()
            all_rtt.append(int((fp-sp)*1000))
            print("ping to "+ip+", seq = "+str(n)+", rtt = "+str(int((fp-sp)*1000))+" ms")

        except:
            print("ping to "+ip+", seq = "+str(n)+", "+"timeout")
        n+=1
    print("minimum = "+str(min(all_rtt))+" ms , maximum = "+str(max(all_rtt))+" ms, average = "+str(sum(all_rtt) / len(all_rtt))+" ms")
    udp_socket.close()

if __name__ == "__main__":
    main()