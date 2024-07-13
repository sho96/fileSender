import time
import socket
import threading
import os
import sys

def sendhuge(client, data) -> None:
    length = len(data)
    client.send(f"{length}\n".encode("ascii"))
    client.sendall(data)

def recvhuge(client) -> bytes:
    startTime = time.perf_counter()
    length = b""
    while True:
        if client.recv(1, socket.MSG_PEEK) == 0:
            continue
        recved = client.recv(1)
        if recved == b'\n':
            break
        length += recved
    length = int(length)
    recved = b''
    while True:
        recved += client.recv(length - len(recved))
        if len(recved) == length:
            break
        precentage = len(recved)/(length/100)
        print(f"\r{round(precentage, 1)} %", end="")
    endTime = time.perf_counter()
    print(f"\r100.0 % received in {round(endTime - startTime, 3)}s")
    return recved

def recvfile(client, path) -> int:
    startTime = time.perf_counter()
    length = b""
    while True:
        if client.recv(1, socket.MSG_PEEK) == 0:
            continue
        recved = client.recv(1)
        if recved == b'\n':
            break
        length += recved
    length = int(length)
    print(f"receiving {length} bytes")
    file = open(path, "wb")
    totalLength = 0
    while True:
        packet = client.recv(length - totalLength)
        file.write(packet)
        totalLength += len(packet)
        if totalLength == length:
            break
        precentage = totalLength/(length/100)
        print(f"\r{round(precentage, 1)} %", end="")
    endTime = time.perf_counter()
    print(f"\r100.0 % received in {round(endTime-startTime, 3)}s")
    return length

def sendfile(client, path):
    with open(path, "rb") as f:
        sendhuge(client, f.read())


def getIP():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(("8.8.8.8", 80))
    ip = s.getsockname()[0]
    s.close()
    return ip

def askForInt(msg, errmsg):
    while True:
        answer = input(msg)
        try:
            return int(answer)
        except TypeError:
            print(errmsg)

def addClientThread(server, activeClients):
    try:
        while True:
            client, addr = server.accept()
            sendhuge(client, b"connected")
            activeClients.append(client)
    except OSError:
        pass

def sendMode():
    ip = getIP()
    port = askForInt("port: ", "not an integer\n")
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((ip, port))
    server.listen()
    print(f"\n-> host listening on ip: {ip} and port: {port}\n")
    activeClients = []
    threading.Thread(target=addClientThread, args=(server, activeClients)).start()
    files = []
    fileheader = "\n    "
    while True:
        print(f"\ncurrently chosen files: {fileheader}{fileheader.join([path for path in files])}")
        path = input("\npath (press enter if done): ")
        if '"' in path:
            path = path.replace('"', "")
        if path == "":
            break
        if not os.path.exists(path):
            print("file doesn't exist")
            continue
        files.append(path)
    input("---press enter to start sending files to clients---")
    for i, path in enumerate(files):
        print(f"\n--------- sending {os.path.basename(path)} to clients ({i+1}/{len(files)}) ----------")
        with open(path, "rb") as f:
            fileContent = f.read()
        for clientIndex, client in enumerate(activeClients):
            print(f"sending to {clientIndex+1}/{len(activeClients)} clients")
            sendhuge(client, b"sendingFile")
            sendhuge(client, os.path.basename(path).encode("utf-8"))
            sendhuge(client, fileContent)
            if i == len(files) - 1:
                sendhuge(client, b"done")
        
    print("\nsent!!")
    server.close()
    sys.exit()

def receiveMode():
    directory = input("path to the directory to download all the files\n-> ")
    if directory == "":
        directory = os.getcwd()

    ip = input("server ip: ")
    port = askForInt("port: ", "not an integer\n")
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect((ip, port))
    while True:
        received = recvhuge(client).decode("utf-8")
        if received == "connected":
            print("connected to server!\nwaiting for host to start sharing files...")
        elif received == "sendingFile":
            filename = recvhuge(client).decode("utf-8")
            print(f"\nreceiving {filename}")
            recvfile(client, os.path.join(directory, filename))
        elif received == "done":
            print(f"\n----- all files received! -----\n")
            break
    print("disconnecting...")
    client.close()
    sys.exit()


def main():
    mode = input("send/receive (s/r)\n-> ")
    if mode == "s":
        sendMode()
    elif mode == "r":
        receiveMode()
    else:
        print("mode not supported")
        main()

if __name__ == "__main__":
    main()