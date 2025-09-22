#!/usr/bin/env python3
"""
Client-Modified.py - Enhanced TCP Client with Robust File/Message Transfer
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
import sys

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

def recv_file(sock, save_path):
    """
    Receive a file with metadata (filename + size + content)
    Protocol: [filename_length][filename][file_size][file_content]
    """
    try:
        # Receive filename
        filename_data = recv_message(sock)
        if not filename_data:
            return False
        
        filename = filename_data.decode('utf-8')
        print(f"📁 Receiving file: {filename}")
        
        # Receive file size (8 bytes)
        file_size_data = recv_exact(sock, 8)
        file_size = struct.unpack('!Q', file_size_data)[0]
        print(f"📏 File size: {file_size:,} bytes")
        
        # Prepare save path
        if save_path.endswith('/') or save_path.endswith('\\'):
            full_save_path = os.path.join(save_path, filename)
        else:
            full_save_path = save_path
        
        # Receive file content
        bytes_received = 0
        chunk_size = 64 * 1024  # 64KB chunks
        
        with open(full_save_path, 'wb') as f:
            while bytes_received < file_size:
                remaining = file_size - bytes_received
                current_chunk_size = min(chunk_size, remaining)
                
                chunk = recv_exact(sock, current_chunk_size)
                f.write(chunk)
                bytes_received += len(chunk)
                
                # Progress indicator
                progress = (bytes_received / file_size) * 100
                print(f"📥 File progress: {bytes_received:,}/{file_size:,} bytes ({progress:.1f}%)")
        
        print(f"✅ File received successfully: {full_save_path}")
        return True
    except Exception as e:
        print(f"❌ Error receiving file: {e}")
        return False

def get_local_ip():
    """Get the local IP address of this machine"""
    try:
        # Connect to a remote address to determine local IP
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("8.8.8.8", 80))
            local_ip = s.getsockname()[0]
        return local_ip
    except:
        return "127.0.0.1"  # Fallback to localhost

def parse_arguments():
    """Parse command line arguments for server connection"""
    default_ip = "tp-1a201-37"  # Default server machine
    default_port = 9000
    
    if len(sys.argv) >= 2:
        server_ip = sys.argv[1]
        if len(sys.argv) >= 3:
            try:
                server_port = int(sys.argv[2])
            except ValueError:
                print("❌ Invalid port number")
                server_port = default_port
        else:
            server_port = default_port
        print(f"🎯 Using command line args: {server_ip}:{server_port}")
    else:
        server_ip = default_ip
        server_port = default_port
        print(f"🎯 Using defaults: {server_ip}:{server_port}")
    
    return server_ip, server_port

def main():
    print("=== Enhanced TP1 TCP Client - Telecom Paris ===")
    print("🚀 Features: Length-prefixed messages, endianness handling, large file support")
    print("💡 Usage: python3 client-modified.py [server_ip] [port]")
    
    # Parse command line arguments
    server_ip, server_port = parse_arguments()
    
    # Client information  
    machine_name = "tp-1a201-40"  # This client represents tp-1a201-40
    client_port = "9001"  # Client's own port (can be different from server port)
    client_ip = get_local_ip()  # Get actual IP address
    
    print(f"📡 Client machine: {machine_name}")
    print(f"📡 Client IP: {client_ip}")
    print(f"📡 Client port: {client_port}")
    print(f"Connecting to enhanced server at {server_ip}:{server_port}...")
    
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
            client_socket.connect((server_ip, server_port))
            print("✅ Connected to enhanced server!")
            
            # Step 1: Receive "Hello" message using robust protocol
            print("📥 Waiting for Hello message...")
            hello_data = recv_message(client_socket)
            
            if hello_data:
                server_message = hello_data.decode('utf-8')
                print(f"📨 Server says: {server_message}")
                
                if server_message == "Hello":
                    print("✅ Received Hello from server!")
                    
                    # Step 2: Send response with Port + Machine + IP using robust protocol
                    client_response = f"{client_port}+{machine_name}+{client_ip}"
                    print(f"📤 Sending response: {client_response}")
                    
                    if send_message(client_socket, client_response):
                        print("✅ Response sent successfully!")
                        
                        # Step 3: Receive large test message
                        print("📥 Waiting for large test message...")
                        large_data = recv_message(client_socket)
                        
                        if large_data:
                            large_message = large_data.decode('utf-8')
                            print(f"📨 Received large message: {len(large_message):,} bytes")
                            print(f"🔍 Message preview: '{large_message[:50]}...'")
                        
                        # Step 4: Try to receive a file (if server sends one)
                        print("📁 Checking for file transfer...")
                        try:
                            # Set a short timeout to check if file is coming
                            client_socket.settimeout(5.0)
                            
                            # Try to receive filename
                            filename_data = recv_message(client_socket)
                            if filename_data:
                                # File is coming, reset timeout and receive it
                                client_socket.settimeout(None)
                                
                                # Put the filename back and receive the full file
                                # (This is a simplified approach - in real implementation, 
                                # you'd have a protocol to indicate file transfer)
                                filename = filename_data.decode('utf-8')
                                print(f"📁 File transfer detected: {filename}")
                                
                                # Receive file size
                                file_size_data = recv_exact(client_socket, 8)
                                file_size = struct.unpack('!Q', file_size_data)[0]
                                print(f"📏 File size: {file_size:,} bytes")
                                
                                # Save file with prefix
                                save_filename = f"received_{filename}"
                                bytes_received = 0
                                
                                with open(save_filename, 'wb') as f:
                                    while bytes_received < file_size:
                                        chunk_size = min(64*1024, file_size - bytes_received)
                                        chunk = recv_exact(client_socket, chunk_size)
                                        f.write(chunk)
                                        bytes_received += len(chunk)
                                        
                                        progress = (bytes_received / file_size) * 100
                                        print(f"📥 File progress: {bytes_received:,}/{file_size:,} bytes ({progress:.1f}%)")
                                
                                print(f"✅ File saved as: {save_filename}")
                                
                        except socket.timeout:
                            print("📝 No file transfer (timeout - normal)")
                        except Exception as file_error:
                            print(f"⚠️ File transfer issue: {file_error}")
                        finally:
                            client_socket.settimeout(None)
                        
                        print("✅ Enhanced protocol completed successfully!")
                        print("🎉 All transfers finished!")
                        
                        # Protocol is complete - exit cleanly
                        return
                    else:
                        print("❌ Failed to send response")
                else:
                    print(f"⚠️ Unexpected message from server: {server_message}")
            else:
                print("❌ No Hello message received from server")
                
    except ConnectionRefusedError:
        print("❌ Connection refused. Make sure enhanced server is running first.")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    print("👋 Enhanced client disconnected")

if __name__ == "__main__":
    main()