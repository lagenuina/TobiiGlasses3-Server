import asyncio
import logging
import socket
import threading
import cv2
import math
from g3pylib import connect_to_glasses
import json

logging.basicConfig(level=logging.INFO)

class TCPServer:
    def __init__(self, ip_address, port):
        self.ip_address = ip_address
        self.port = port
        self.server = None
        self.running = False
        self.client_sockets = []

    def start_server(self):
        try:
            # Initialize and start the server
            self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server.bind((self.ip_address, self.port))
            self.server.listen(5)  # Listen for up to 5 connections
            self.running = True
            print(f"Server started at {self.ip_address}:{self.port}")
            threading.Thread(target=self.accept_clients, daemon=True).start()
        except Exception as e:
            print(f"Error starting server: {e}")

    def accept_clients(self):
        while self.running:
            try:
                client_socket, client_address = self.server.accept()
                self.client_sockets.append(client_socket)
                print(f"Client connected from {client_address}")
            except Exception as e:
                print(f"Error accepting client connection: {e}")

    def broadcast(self, data):
        for client_socket in self.client_sockets:
            try:
                client_socket.sendall(data)
            except Exception as e:
                print(f"Error sending data to client: {e}")
                self.client_sockets.remove(client_socket)

    def stop_server(self):
        self.running = False
        for client_socket in self.client_sockets:
            client_socket.close()
        if self.server:
            self.server.close()
        print("Server stopped.")

def send_frame_udp(frame, frame_num, udp_ip, udp_port, chunk_size):
    """Send the encoded frame over UDP in chunks."""
    # Create UDP socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    # Encode the frame
    encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), 90]
    data_string = cv2.imencode('.jpg', frame, encode_param)[1].tostring()
    frame_size = len(data_string)

    # Calculate the number of chunks
    max_chunks = math.ceil(frame_size / chunk_size)
    current_ind = 0
    current_chunk = 0

    while current_ind < frame_size:
        payload_size = chunk_size
        if current_ind + chunk_size > frame_size:
            payload_size = frame_size - current_ind

        payload = data_string[current_ind:current_ind + payload_size]
        header = f"{frame_num}_{current_chunk}_{max_chunks}_{current_ind}_{payload_size}_{frame_size}"
        packet = bytes(header, "utf-8") + bytes(1) + payload
        sock.sendto(packet, (udp_ip, udp_port))

        current_chunk += 1
        current_ind += chunk_size

async def stream_rtsp(tcp_server, udp_ip, udp_port, chunk_size):
    async with connect_to_glasses.with_hostname('192.168.75.51') as g3:
        async with g3.stream_rtsp(scene_camera=True, gaze=True) as streams:
            async with streams.gaze.decode() as gaze_stream, streams.scene_camera.decode() as scene_stream:
                frame_num = 0
                while True:
                    frame, frame_timestamp = await scene_stream.get()
                    gaze, gaze_timestamp = await gaze_stream.get()
                    while gaze_timestamp is None or frame_timestamp is None:
                        if frame_timestamp is None:
                            frame, frame_timestamp = await scene_stream.get()
                        if gaze_timestamp is None:
                            gaze, gaze_timestamp = await gaze_stream.get()
                    while gaze_timestamp < frame_timestamp:
                        gaze, gaze_timestamp = await gaze_stream.get()
                        while gaze_timestamp is None:
                            gaze, gaze_timestamp = await gaze_stream.get()

                    frame = frame.to_ndarray(format="bgr24")

                    # If given gaze data
                    if "gaze2d" in gaze:
                        gaze2d = gaze["gaze2d"]

                        # Convert rational (x,y) to pixel location (x,y)
                        h, w = frame.shape[:2]
                        fix = (int(gaze2d[0] * w), int(gaze2d[1] * h))

                        # Draw gaze
                        frame = cv2.circle(frame, fix, 10, (0, 0, 255), 3)

                        gaze['gazePixelCoords'] = fix

                    # Send the entire gaze dictionary as JSON
                    if gaze:
                        # Send JSON data to Unity
                        tcp_server.broadcast((json.dumps(gaze) + '\n').encode('utf-8'))
                    
                    frame = cv2.resize(frame, (640, 480))
                    # Send frame over UDP
                    send_frame_udp(frame, frame_num, udp_ip, udp_port, chunk_size)

                    frame_num += 1

def main():
    # Start the TCP server
    tcp_server = TCPServer("127.0.0.1", 5555)
    tcp_server.start_server()

    # UDP configuration
    udp_ip = "127.0.0.1"  # Change to your UDP server's IP
    udp_port = 8080      # Change to your UDP server's port
    chunk_size = 4000    # Adjust chunk size as needed

    try:
        asyncio.run(stream_rtsp(tcp_server, udp_ip, udp_port, chunk_size))
    except KeyboardInterrupt:
        print("Shutting down...")
    finally:
        tcp_server.stop_server()


if __name__ == "__main__":
    main()
