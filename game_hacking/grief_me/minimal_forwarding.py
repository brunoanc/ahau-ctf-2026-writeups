#!/usr/bin/env python3

import socket
import threading
import uuid


LISTEN_HOST = "127.0.0.1"
LISTEN_PORT = 25570

BACKEND_HOST = "79.127.180.10"
BACKEND_PORT = 62274

FORWARDED_IP = "127.0.0.1"


def encode_varint(value):
    result = bytearray()

    while True:
        byte = value & 0x7F
        value >>= 7

        if value:
            byte |= 0x80

        result.append(byte)

        if not value:
            return bytes(result)


def decode_varint(data, offset=0):
    value = 0

    for position in range(0, 35, 7):
        byte = data[offset]
        offset += 1
        value |= (byte & 0x7F) << position

        if not byte & 0x80:
            return value, offset

    raise ValueError("VarInt inválido")


def receive_varint(sock):
    value = 0

    for position in range(0, 35, 7):
        byte = sock.recv(1)

        if not byte:
            raise ConnectionError("Conexión cerrada")

        value |= (byte[0] & 0x7F) << position

        if not byte[0] & 0x80:
            return value

    raise ValueError("VarInt inválido")


def receive_exact(sock, length):
    result = bytearray()

    while len(result) < length:
        chunk = sock.recv(length - len(result))

        if not chunk:
            raise ConnectionError("Conexión cerrada")

        result.extend(chunk)

    return bytes(result)


def decode_string(data, offset):
    length, offset = decode_varint(data, offset)
    end = offset + length
    return data[offset:end].decode("utf-8"), end


def encode_string(value):
    encoded = value.encode("utf-8")
    return encode_varint(len(encoded)) + encoded


def parse_handshake(handshake):
    packet_id, offset = decode_varint(handshake)
    protocol, offset = decode_varint(handshake, offset)
    hostname, offset = decode_string(handshake, offset)
    port = handshake[offset:offset + 2]
    offset += 2
    next_state, offset = decode_varint(handshake, offset)

    return packet_id, protocol, hostname, port, next_state


def parse_login_identity(login_start):
    packet_id, offset = decode_varint(login_start)

    if packet_id != 0:
        raise ValueError("Se esperaba Login Start")

    username, offset = decode_string(login_start, offset)
    player_uuid = uuid.UUID(bytes=login_start[offset:offset + 16])
    return username, player_uuid


def add_forwarding(handshake, player_uuid):
    packet_id, protocol, hostname, port, next_state = parse_handshake(handshake)

    if packet_id != 0 or next_state != 2:
        raise ValueError("Handshake de login inválido")

    forwarded_hostname = (
        hostname
        + "\x00"
        + FORWARDED_IP
        + "\x00"
        + player_uuid.hex
        + "\x00[]"
    )

    return (
        encode_varint(0)
        + encode_varint(protocol)
        + encode_string(forwarded_hostname)
        + port
        + encode_varint(next_state)
    )


def relay(source, destination):
    try:
        while data := source.recv(65535):
            destination.sendall(data)
    except OSError:
        pass

    try:
        destination.shutdown(socket.SHUT_WR)
    except OSError:
        pass


def handle(client):
    backend = socket.create_connection((BACKEND_HOST, BACKEND_PORT), timeout=10)

    try:
        length = receive_varint(client)
        handshake = receive_exact(client, length)
        _, _, _, _, next_state = parse_handshake(handshake)

        if next_state == 1:
            backend.sendall(encode_varint(len(handshake)) + handshake)
        else:
            login_length = receive_varint(client)
            login_start = receive_exact(client, login_length)
            username, player_uuid = parse_login_identity(login_start)
            handshake = add_forwarding(handshake, player_uuid)

            backend.sendall(encode_varint(len(handshake)) + handshake)
            backend.sendall(encode_varint(len(login_start)) + login_start)
            print(f"Conexión: {username} ({player_uuid})")

        client.settimeout(None)
        backend.settimeout(None)

        client_to_backend = threading.Thread(
            target=relay, args=(client, backend), daemon=True
        )
        backend_to_client = threading.Thread(
            target=relay, args=(backend, client), daemon=True
        )

        client_to_backend.start()
        backend_to_client.start()
        client_to_backend.join()
        backend_to_client.join()
    finally:
        client.close()
        backend.close()


def main():
    with socket.create_server((LISTEN_HOST, LISTEN_PORT)) as listener:
        print(f"Minecraft: {LISTEN_HOST}:{LISTEN_PORT}")
        print(f"Backend:   {BACKEND_HOST}:{BACKEND_PORT}")

        while True:
            client, _ = listener.accept()
            threading.Thread(target=handle, args=(client,), daemon=True).start()


if __name__ == "__main__":
    main()
