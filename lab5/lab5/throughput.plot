set term png
set output "TCPThroughput.png"

set title "TCP Throughput for Flows Terminating at Node n5"
set xlabel "Time (seconds)"
set ylabel "Throughput (MBit/s)"

plot "tcp1.tr" using 1:2 with lines title "Flow 1", \
     "tcp2.tr" using 1:2 with lines title "Flow 2"

