import socket
import sys


def main():
    args = sys.argv
    port = int(args[1])
    tcp_server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    tcp_server_socket.bind(("127.0.0.1", port))
    tcp_server_socket.listen(128)

    while True:
        new_client_socket, client_addr = tcp_server_socket.accept()
        recv_data = new_client_socket.recv(1024)

        if recv_data :
            request_lines = recv_data.decode().split("\r\n")

            if not request_lines[0].startswith("GET"):
                new_client_socket.send(b"HTTP/1.1 404 Not Found\r\n\r\n")
                return


            requested_file_path = request_lines[0].split()[1]

            try:
                with open("." + requested_file_path, "rb") as file:
                    file_content = file.read()
                    response_headers = "HTTP/1.1 200 OK\r\nContent-Length: {}\r\n\r\n".format(len(file_content))
                    new_client_socket.send(response_headers.encode() + file_content)
            except FileNotFoundError:
                new_client_socket.send(b"HTTP/1.1 404 Not Found\r\n\r\n")

        new_client_socket.close()

    tcp_server_socket.close()


if __name__ == "__main__":
    main()