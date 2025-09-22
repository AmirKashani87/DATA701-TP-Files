#!/usr/bin/env python3
"""
Server-Modified.py - Enhanced TCP Server with Robust File/Message Transfer
Implements length-prefixed protocol with endianness handling for large transfers
Features:
- Length-prefixed messages (4-byte header)
- Network byte order (big-endian)
- Complete data reception guarantees
- Large file transfer support
- Metadata tracking
"""

import socket
import struct
import os
import time

def send_message(sock, message):
    """
    Send a message with length prefix (robust transmission)
    Protocol: [4-byte length][message data]
    Length is in network byte order (big-endian)
    """
    try:
        # Encode message to bytes
        if isinstance(message, str):
            message_bytes = message.encode('utf-8')
        else:
            message_bytes = message
        
        # Get message length
        message_length = len(message_bytes)
        
        # Pack length as 4-byte unsigned integer in network byte order (big-endian)
        length_header = struct.pack('!I', message_length)  # '!' = network byte order
        
        # Send length header first (4 bytes)
        sock.sendall(length_header)
        print(f"📏 Sent length header: {message_length} bytes")
        
        # Send the actual message data
        sock.sendall(message_bytes)
        print(f"📤 Sent message: {message_length} bytes")
        
        return True
    except Exception as e:
        print(f"❌ Error sending message: {e}")
        return False

def recv_exact(sock, n_bytes):
    """
    Receive exactly n_bytes from socket (guaranteed complete reception)
    Handles partial receives that can happen with TCP
    """
    data = b''
    bytes_remaining = n_bytes
    
    while bytes_remaining > 0:
        chunk = sock.recv(bytes_remaining)
        if not chunk:
            raise ConnectionError("Connection closed unexpectedly")
        
        data += chunk
        bytes_remaining -= len(chunk)
        
        if bytes_remaining > 0:
            print(f"📥 Partial receive: {len(chunk)} bytes, {bytes_remaining} remaining")
    
    return data

def recv_message(sock):
    """
    Receive a length-prefixed message (robust reception)
    Protocol: [4-byte length][message data]
    Returns the message as bytes
    """
    try:
        # First, receive the 4-byte length header
        length_header = recv_exact(sock, 4)
        
        # Unpack length from network byte order (big-endian)
        message_length = struct.unpack('!I', length_header)[0]
        print(f"📏 Expected message length: {message_length} bytes")
        
        # Validate message length (prevent memory attacks)
        if message_length > 1024 * 1024 * 100:  # 100MB limit
            raise ValueError(f"Message too large: {message_length} bytes")
        
        # Receive the exact amount of message data
        message_data = recv_exact(sock, message_length)
        print(f"📥 Received complete message: {len(message_data)} bytes")
        
        return message_data
    except Exception as e:
        print(f"❌ Error receiving message: {e}")
        return None

def send_file(sock, file_path):
    """
    Send a file with metadata (filename + size + content)
    Protocol: [filename_length][filename][file_size][file_content]
    """
    try:
        if not os.path.exists(file_path):
            print(f"❌ File not found: {file_path}")
            return False
        
        file_size = os.path.getsize(file_path)
        filename = os.path.basename(file_path)
        
        print(f"📁 Preparing to send file:")
        print(f"   Name: {filename}")
        print(f"   Size: {file_size:,} bytes")
        
        # Send filename first
        if not send_message(sock, filename):
            return False
        
        # Send file size as metadata
        file_size_bytes = struct.pack('!Q', file_size)  # 8-byte unsigned long
        sock.sendall(file_size_bytes)
        print(f"📏 Sent file size: {file_size:,} bytes")
        
        # Send file content in chunks
        bytes_sent = 0
        chunk_size = 64 * 1024  # 64KB chunks
        
        with open(file_path, 'rb') as f:
            while bytes_sent < file_size:
                remaining = file_size - bytes_sent
                current_chunk_size = min(chunk_size, remaining)
                
                chunk = f.read(current_chunk_size)
                if not chunk:
                    break
                
                sock.sendall(chunk)
                bytes_sent += len(chunk)
                
                # Progress indicator
                progress = (bytes_sent / file_size) * 100
                print(f"📤 File progress: {bytes_sent:,}/{file_size:,} bytes ({progress:.1f}%)")
        
        print(f"✅ File sent successfully: {bytes_sent:,} bytes")
        return True
    except Exception as e:
        print(f"❌ Error sending file: {e}")
        return False

def main():
    print("=== Enhanced TP1 TCP Server - Telecom Paris ===")
    print("🚀 Features: Length-prefixed messages, endianness handling, large file support")
    
    # Server configuration
    host = ''  # Listen on all interfaces
    port = 9000
    machine_name = "tp-1a201-37"  # This server represents tp-1a201-37
    
    print(f"Starting enhanced server on port {port}...")
    print(f"📡 Machine: {machine_name}")
    
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_socket.bind((host, port))
        server_socket.listen(1)
        
        print("🔵 Enhanced server ready and listening...")
        print("⏳ Waiting for client connection...")
        
        conn, addr = server_socket.accept()
        with conn:
            print(f"✅ Client connected from {addr}")
            
            # Step 1: Send "Hello" using robust protocol
            hello_message = "Hello"
            print(f"📤 Sending Hello message...")
            if not send_message(conn, hello_message):
                print("❌ Failed to send Hello message")
                return
            
            # Step 2: Receive client response using robust protocol
            print("📥 Waiting for client response...")
            client_data = recv_message(conn)
            
            if client_data:
                client_response = client_data.decode('utf-8')
                print(f"📨 Client response: {client_response}")
                
                # Parse client response (Port+Machine+IP)
                if '+' in client_response:
                    parts = client_response.split('+')
                    if len(parts) == 3:
                        client_port = parts[0]
                        client_machine = parts[1]
                        client_ip = parts[2]
                        
                        print(f"📋 Parsed client info:")
                        print(f"   Port: {client_port}")
                        print(f"   Machine: {client_machine}")
                        print(f"   IP: {client_ip}")
                        
                        print("✅ Enhanced handshake successful!")
                        
                        # Step 3: Demonstrate large message capability
                        large_message = "This is a large test message! " * 1000  # ~30KB message
                        print(f"📤 Sending large test message ({len(large_message)} bytes)...")
                        
                        if send_message(conn, large_message):
                            print("✅ Large message sent successfully!")
                        
                        # Optional: Send a file if it exists
                        test_file = "test_file.txt"
                        if os.path.exists(test_file):
                            print(f"📁 Test file found, sending: {test_file}")
                            send_file(conn, test_file)
                        
                        print("🎉 Enhanced protocol completed successfully!")
                    else:
                        print("❌ Invalid client response format (expected: Port+Machine+IP)")
                        send_message(conn, "ERROR: Invalid format")
                else:
                    print("❌ Invalid client response format (missing + separator)")
                    send_message(conn, "ERROR: Missing separator")
            else:
                print("❌ No valid response received from client")
    
    print("👋 Enhanced server shutdown")

if __name__ == "__main__":
    main()