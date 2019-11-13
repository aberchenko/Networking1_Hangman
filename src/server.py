# server.py

from socket import *
from signal import signal, SIGINT

import sys
import random
import threading
import time

debugging = False
words = []
maxIncorrect = 6

ip = '127.0.0.1'
port = '9012'

serverSocket = None

maxConnections = 3
connections = []

def debug(*messages):
    if debugging:
        for message in messages:
            print(message, end=" ")
        print("")

def closeHandler(signal_received, frame):
    debug("Received close signal")
    global serverSocket
    serverSocket.close()
    for connection in connections:
        if connection != None:
            connection.endConnection()
    sys.exit(0)

def readWords():
    try:
        wordFile = open("../word.txt", "r")

        try:
            for line in wordFile:
                line = line.strip()
                words.append(line)

        finally:
            wordFile.close()
    except:
        print("Unable to find word.txt")

def initializeConnections():
    for _ in range(maxConnections):
        connections.append(None)

def addConnection(newConnection):
    for i in range(maxConnections):
        if connections[i] == None:
            connections[i] = newConnection
            return i
    return -1

class Game:
    def __init__(self):
        wordIndex = random.randint(0, len(words)-1)
        self.word = words[wordIndex]
        self.guesses = []

        print(self.word)

    def guess(self, letter):
        self.guesses.append(letter)

        if self.numWrongGuesses() >= maxIncorrect:
            return "You Lose!"
        elif self.finishedWord():
            return "You Win!"
    
    def numWrongGuesses(self):
        wrongGuesses = 0
        for guess in self.guesses:
            if guess not in self.word:
                wrongGuesses += 1
        return wrongGuesses

    def finishedWord(self):
        for letter in self.word:
            if letter not in self.guesses:
                return False
        return True
        
    def getWordSoFar(self):
        wordSoFar = ""
        for letter in self.word:
            if letter in self.guesses:
                wordSoFar += letter
            else:
                wordSoFar += "-"
        return wordSoFar

class Connection:
    def __init__(self, socket, addr):
        self.socket = socket
        self.addr = addr
        self.game = Game()

    def startGame(self, index):
        self.index = index
        thread = threading.Thread(target=self.startGameAsync, args=[])
        thread.start()

    def startGameAsync(self):
        debug("Game starting")
        message = self.socket.recv(1024)
        debug("Received initial message:", message)
        self.sendGuessResult()
        self.connection_loop()

    def connection_loop(self):
        while True:
            message = self.socket.recv(1024)
            debug("Received message:", message)
            letter = self.decodeMessage(message)
            if self.receiveGuess(letter):
                break

    def receiveGuess(self, guess):
        result = self.game.guess(guess)
        debug("Result of guess:", result)
        self.sendGuessResult()
        if result != None:
            time.sleep(0.1)
            self.sendMessage(result)
            self.endConnection()
            return True
        else:
            return False

    def sendGuessResult(self):
        numWrongGuesses = self.game.numWrongGuesses()
        wordSoFar = self.game.getWordSoFar()
        wordLength = len(wordSoFar)

        flagBytes = (0).to_bytes(1, 'big')
        lengthBytes = wordLength.to_bytes(1, 'big')
        wrongBytes = numWrongGuesses.to_bytes(1, 'big')
        wordBytes = wordSoFar.encode()

        message = flagBytes + lengthBytes + wrongBytes + wordBytes
        debug("Sending:", message)
        self.socket.send(message)

    def decodeMessage(self, message):
        if len(message) == 0:
            return None
        else:
            length = message[0]
            letter = message[1:1+length].decode()
            return letter

    def sendMessage(self, message):
        bytesMessage = message.encode()
        messageLength = len(bytesMessage)
        bytesMessage = messageLength.to_bytes(1, 'big') + bytesMessage
        debug("Sending:", bytesMessage)
        self.socket.send(bytesMessage)

    def failConnection(self):
        debug('Server overloaded')
        thread = threading.Thread(target=self.failConnectionAsync, args=[])
        thread.start()

    def failConnectionAsync(self):
        self.sendMessage('server-overloaded')
        self.endConnection()

    def endConnection(self):
        self.socket.close()
        connections[self.index] = None
        debug("Connection ended")

def server_loop():
    global serverSocket
    serverSocket = socket(AF_INET, SOCK_STREAM)
    signal(SIGINT, closeHandler)
    serverSocket.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
    serverSocket.bind((ip, int(port)))
    serverSocket.listen(1)
    debug('Server is listening')
    while True:
        connectionSocket, addr = serverSocket.accept()
        connection = Connection(connectionSocket, addr)
        index = addConnection(connection)
        if index == -1:
            connection.failConnection()
        else:
            connection.startGame(index)

if __name__ == '__main__':

    for i in range(len(sys.argv)):
        if sys.argv[i] == '-D':
            debugging = True
            continue
        
        if not debugging:
            if i == 1:
                ip = sys.argv[i]
            elif i == 2:
                port = sys.argv[i]
        else:
            if i == 2:
                ip = sys.argv[i]
            elif i == 3:
                port = sys.argv[i]

    readWords()
    initializeConnections()

    debug("Started")

    server_loop()