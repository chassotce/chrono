import serial
import threading
from app import db, app
from models import Participant
from sqlalchemy.sql import exists


class RS232captureThread(threading.Thread):
    # configure the serial connection
    global ser
    '''
    ser = serial.Serial(
        port="/dev/ttyUSB0",
        baudrate=1200,
        parity=serial.PARITY_EVEN,
        stopbits=serial.STOPBITS_ONE,
        bytesize=serial.EIGHTBITS
    )'''

    oldPacket = ""

    penaltyTime = 0
    global hundredNumberRunner
    hundredNumberRunner = 0

    global SYNCHRO
    global BLANK
    SYNCHRO = "ff"
    BLANK = "aa"

    #ser.open()
    #ser.setRTS(True) TO USE LATER

    #ser.setDTR(True)  #confirms the connection
    print "DTR is set on 1 now"

    global testPacketParcours
    testPacketParcours = "aa28000404000000aa1aa2aaaa0000ff"
    testPacketClassement = "2553000404000000aa1aa1aaaa0000ff".decode("hex")

    def __init__(self):
        threading.Thread.__init__(self)

    def checkPCCommand(pcCommand, currNumber):
        options = {2: "eliminated",
                   3: "gaveUp",
                   4: "HC",
                   9: "incrTime",
                   11: "IncrNumByHundred",
                   12: "isBarrage",
        }
        options[pcCommand]()

        def eliminated():
            db.session.query(Participant).filter_by(num_depart=currNumber).update(
                {"etat": "elimine"})

        def gaveUp():
            db.session.query(Participant).filter_by(num_depart=currNumber).update(
                {"etat": "abandon"})

        def HC():
            db.session.query(Participant).filter_by(num_depart=currNumber).update(
                {"hc": True})

        def incrTime():
            self.penaltyTime += 100  #Bareme C, bareme A adds points

        def IncrNumByHundred():
            hundredNumberRunner += 1

        def isBarrage():  #useless if the sqlalchemy requests are correct
            nothing = 0

    def saveRunner(self, currentPacket):

        currentPacket = currentPacket.replace("a", "0")
        print currentPacket

        currentPen = int(currentPacket[6:8])
        currentTime = int(currentPacket[0:4]) + self.penaltyTime  #TODO : deal with the fifth number (also seconds)
        currentNumber = int(currentPacket[21] + currentPacket[18]) + 100 * hundredNumberRunner

        print "Current Number : {0} , current time : {1} , current penalties : {2}".format(str(currentNumber),
                                                                                           str(currentTime),
                                                                                           str(currentPen))

        app.config["CURRENT_EPREUVE_ID"]=5
        currentRunner=db.session.query(Participant).filter(Participant.num_depart == currentNumber
                    and Participant.id_epreuve == app.config["CURRENT_EPREUVE_ID"])

        print db.session.query(currentRunner.exists()).all()
        if "True" in str(db.session.query(currentRunner.exists()).all()):
            print "Runner already in db"

            if currentRunner.temps_init == 0: #No temps_init for an object Query
                print "Runner now has time_init"
                currentRunner.update(
                    {"points_init": currentPen}, {"temps_init": currentTime})

            elif currentRunner.temps_barr == 0:
                print "Runner now has time_barr"
                currentRunner.update(
                    {"points_barr": currentPen}, {"temps_barr": currentTime})

            else:
                print "Runner now has time_barr2"
                currentRunner.update(
                    {"points_barr2": currentPen}, {"temps_barr2": currentTime})

        else:
            print "Runner not in db, creating him"
            runnerToAdd = Participant(
                num_depart=currentNumber, points_init=currentPen, temps_init=currentTime,
                id_epreuve=app.config["CURRENT_EPREUVE_ID"])
            db.session.add(runnerToAdd)
        db.session.commit()
        penaltyTime = 0

    def capture(self):
        currentPacket = ""
        currentChar = ""
        while currentChar != SYNCHRO:
            currentPacket += currentChar
            currentChar = ser.read(1).encode("hex")
        print currentPacket
        if currentPacket[6] != 0:
            self.checkPCCommand(currentPacket[6], int(currentPacket[22] + currentPacket[19]))
        if self.oldPacket != currentPacket:
            oldPacket = currentPacket
            if currentPacket[0:1] != BLANK:
                self.saveRunner(currentPacket)

    def run(self):
        self.saveRunner(testPacketParcours)
        print "testPacketParcours was handled"
        # while True:
        # self.capture()
        #ser.flush()
        #ser.close()
        #exit()


class RS232SendThread(threading.Thread):
    def getRankFrame(rank):
        if rank < 10:
            frame = "bccb0d0" + str(rank) + "0000000000000000000000ff"
            return frame.decode("hex")
        else:
            frame = "bccb0d" + str(rank) + "0000000000000000000000ff"
            return frame.decode("hex")

    def getPointFrame(point):
        frame = "000000" "d0" + "0000000000000000000000ff"  #PO at the start
        return frame.decode("hex")

    def getOverlappingFrame(overlap):
        frame = "000000" "bd" + "0000000000000000000000ff"  #dE at the start
        return frame.decode("hex")

    def run(self):
        return 0
