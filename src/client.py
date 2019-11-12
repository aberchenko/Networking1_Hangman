# client.py

from socket import *

import sys

debugging = False
maxIncorrect = 6

ip = '127.0.0.1'
port = '9012'

def debug(*messages):
    if debugging:
        for message in messages:
            print(message, end=" ")
        print("")

class Connection:
    def __init__(self, socket):
        self.socket = socket
        self.guesses = []
        self.wrongGuesses = []

        self.sendMessage("")
        self.gameLoop()

    def gameLoop(self):
        while True:
            gameInfo = self.receiveMessage()
            if gameInfo[0] == 0:
                self.printWord(gameInfo[3])
                self.processResult(gameInfo)
                self.printWrongGuesses()
            else:
                print(gameInfo[1])
                self.endConnection()
                break

            if len(self.wrongGuesses) < maxIncorrect and "-" in gameInfo[3]:
                letter = self.getGuess()
                self.guesses.append(letter)
                self.sendMessage(letter)

    def getGuess(self):
        finalLetter = ''
        foundLetter = False
        while not foundLetter:
            print("Letter to guess:", end=" ")
            letter = input()
            verifiedLetter = self.verifyLetter(letter)
            debug("Verified Letter:", verifiedLetter)
            if verifiedLetter == '':
                print("Error! Please guess one letter.")
            else:
                if verifiedLetter in self.guesses:
                    print("Error! Letter", verifiedLetter, "has been guessed before, please guess another letter.")
                else:
                    finalLetter = verifiedLetter
                    foundLetter = True

        return finalLetter

    def printWord(self, word):
        for letter in word:
            print(letter, end=" ")
        print("")

    def printWrongGuesses(self):
        print("Incorrect Guesses:", end="")
        for letter in self.wrongGuesses:
            print(" " + letter, end="")
        print("\n")

    def verifyLetter(self, letter):
        if len(letter) != 1:
            return ''
        lower = letter.lower()
        if lower >= 'a' and lower <= 'z':
            return lower
        else:
            return ''

    def processResult(self, gameInfo):
        if gameInfo[2] > len(self.wrongGuesses):
            self.wrongGuesses.append(self.guesses[-1])

    def sendMessage(self, message):
        messageBytes = message.encode()
        lengthBytes = (len(messageBytes)).to_bytes(1, 'big')

        finalMessage = lengthBytes + messageBytes
        self.socket.send(finalMessage)

    def receiveMessage(self):
        message = self.socket.recv(1024)
        debug("Received message:", message)
        return self.processIncomingMessage(message)

    def processIncomingMessage(self, rawMessage):
        flag = rawMessage[0]
        if flag != 0:
            message = rawMessage[1:1+flag].decode()
            return [flag, message]
        else:
            wordLength = rawMessage[1]
            numIncorrect = rawMessage[2]
            word = rawMessage[3:3+wordLength].decode()
            return [flag, wordLength, numIncorrect, word]

    def endConnection(self):
        self.socket.close()

def startGame():
    print("Ready to start game? (y/n):", end=" ")
    answer = input()
    if answer == 'y':
        clientSocket = socket(AF_INET, SOCK_STREAM)
        clientSocket.connect((ip, int(port)))
        Connection(clientSocket)

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
    
    startGame()