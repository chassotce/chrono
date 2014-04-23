import serial
import threading
from app import db, app, bareme
from models import Participant, Epreuve
from sqlalchemy.sql import exists
import time


class RS232captureThread(threading.Thread):
    # configure the serial connection

    isConnected = False
    while not isConnected:
        try:
            isConnected = True
            ser = serial.Serial(
                port="/dev/ttyUSB0",
                baudrate=1200,
                parity=serial.PARITY_EVEN,
                stopbits=serial.STOPBITS_ONE,
                bytesize=serial.EIGHTBITS
            )
        except:
            print "Serial connection problem"
            isConnected = False
            time.sleep(5)

    oldPacket = ""
    currentNumber = 0
    scorePacket = ""
    isRunning = False

    SYNCHRO = "ff"
    BLANK = "aa"

    ser.flush()
    ser.close()
    ser.open()

    if ser.isOpen():
        app.config["CHRONO_CONNECT"] = True
        print "the serial connection is now open"
    else:
        print "the serial connection is not opened"

    ser.setDTR(True)  #confirms the connection
    ser.setRTS(False)
    print "DTR is set on true now and RTS on false"


    def ishex(self, val):  #from https://coderwall.com/p/bfqwba
        try:
            int(val, 16)
            return True
        except ValueError, e:
            return False

    def getRankPacket(self, rank):
        if rank < 10:
            return "bccb0d0" + str(rank) + "0000000000000000000000ff"
        else:
            return "bccb0d" + str(rank) + "0000000000000000000000ff"

    def getPointPacket(self, point):  #Not currently used
        return "000000" "d0" + "0000000000000000000000ff"  #PO at the start


    def getOverlappingPacket(self, overlap):  #Not currently used
        return "000000" "bd" + "0000000000000000000000ff"  #dE at the start

    def checkRunner(self):
        checkingRunner = db.session.query(Participant).filter(Participant.num_depart == self.currentNumber
                                                              and Participant.id_epreuve == app.config[
                                                                  "CURRENT_EPREUVE_ID"])
        if "True" in str(db.session.query(checkingRunner.exists()).all()):
            return
        else:
            runnerToAdd = Participant(
                num_depart=self.currentNumber, id_epreuve=app.config["CURRENT_EPREUVE_ID"])
            db.session.add(runnerToAdd)
            db.session.commit()
            return


    def getRunner(self):
        return db.session.query(Participant).filter(Participant.num_depart == self.currentNumber
                                                    and Participant.id_epreuve == app.config[
                                                        "CURRENT_EPREUVE_ID"]).first()

    def checkPCCommand(self):

        currRunner = self.getRunner()

        def nothing():
            return

        def reset():
            if self.oldPacket[0] != self.BLANK[0] and self.isRunning:
                print "Launching saveRunner..."
                self.saveRunner()
                if app.config["SEND_AFF"]:
                    self.display()

        def eliminated():
            if currRunner.temps_init == 0:
                currRunner.etat_init = "elimine"
            elif currRunner.temps_barr == 0:
                currRunner.etat_barr = "elimine"
            else:
                currRunner.etat_barr2 = "elimine"
            db.session.commit()

        def gaveUp():
            if currRunner.temps_init == 0:
                currRunner.etat_init = "abandon"
            elif currRunner.temps_barr == 0:
                currRunner.etat_barr = "abandon"
            else:
                currRunner.etat_barr2 = "abandon"
            db.session.commit()

        def HC():
            currRunner.hc = True
            db.session.commit()

        def changeNumber():
            if self.oldPacket[6:8].isdigit():
                self.currentNumber = int(self.oldPacket[6:8])
                self.checkRunner()
                print "Number is now : ", self.currentNumber

        def IncrNumByHundred():
            self.currentNumber += 100
            print "Increased Number is now : ", self.currentNumber
            time.sleep(0.8)
            self.ser.flushInput()

        def ldbarr():
            self.saveRunner()
            return

        options = {'0': nothing,
                   '1': reset,
                   '2': eliminated,
                   '3': gaveUp,
                   '4': HC,
                   '5': nothing,
                   '6': nothing,
                   '7': changeNumber,
                   '8': nothing,
                   '9': nothing,
                   'a': nothing,
                   'b': IncrNumByHundred,
                   'c': nothing,
                   'd': ldbarr,
                   'e': nothing,
                   'f': nothing
        }
        options[self.oldPacket[4]]()


    def display(self):
        if self.scorePacket is '000000000000000000000000000000':
            return
        self.ser.setRTS(True)
        print "RTS set on true. Now displaying for runner number : ", self.currentNumber

        currentCode = db.session.query(Epreuve).filter(Epreuve.id_epreuve == app.config["CURRENT_EPREUVE_ID"]) \
            .first().bareme_code

        res = bareme.Baremes.doBaremes(currentCode)
        infos = next((item for item in res if item["num_depart"] == self.currentNumber),
                     None)  #In case more infos are needed
        rankPacket = self.getRankPacket(infos["rang"])
        rankPacket = rankPacket.decode("hex")

        time_display = app.config["TMP_AFF_TEMPS"] * 1000
        rank_display = app.config["TMP_AFF_CLASSEMENT"] * 1000

        print "Now displaying time"
        timePacket = (self.scorePacket + "ff")
        print str(timePacket)
        timePacket = timePacket.decode("hex")
        display_time = int(round(time.time() * 1000)) + time_display

        while display_time > int(round(time.time() * 1000)):  #TODO: Check if that fits the planned time
            self.ser.write(timePacket)

        print "Now displaying Ranking"

        display_time = int(round(time.time() * 1000)) + rank_display
        while display_time > int(round(time.time() * 1000)):
            self.ser.write(rankPacket)
        self.ser.setRTS(False)
        print "Display finished. RTS set on false."
        self.scorePacket = ""
        return

    def saveRunner(self):

        currentPacket = self.scorePacket.replace("a", "0")
        print "Now working with packet : ", currentPacket

        currentPen = int(currentPacket[6:8])
        currentTime = int(currentPacket[5] + currentPacket[2:4] + currentPacket[0:2])
        if currentTime < int(app.config["TMP_CHARGE_CHRONO"]) * 100:
            self.scorePacket= '000000000000000000000000000000'
            return
        print "Current Number : {0} , current time : {1} , current penalties : {2}".format(str(self.currentNumber),
                                                                                           str(currentTime),
                                                                                           str(currentPen))
        self.checkRunner()
        currentRunner = self.getRunner()

        if currentRunner.temps_init is None or currentRunner.temps_init is 0:
            print "Time_init will be added"
            currentRunner.points_init = currentPen
            currentRunner.temps_init = currentTime
            db.session.commit()

        elif currentRunner.temps_barr is None or currentRunner.temps_barr is 0:
            print "Time_barr will be added"
            currentRunner.points_barr = currentPen
            currentRunner.temps_barr = currentTime
            db.session.commit()

        else:
            print "Time_barr2 will be added/modified"
            currentRunner.points_barr2 = currentPen
            currentRunner.temps_barr2 = currentTime
            db.session.commit()

        if not app.config["SEND_AFF"]:
            self.isRunning = False
        return 0

    def capture(self):
        currentPacket = ""
        currentChar = ""
        firstSynchro = self.ser.read(1).encode("hex")
        while firstSynchro != self.SYNCHRO:
            firstSynchro = self.ser.read(1).encode("hex")
        while currentChar != self.SYNCHRO:
            currentPacket += currentChar
            currentChar = self.ser.read(1).encode("hex")
        print "Packet : ", currentPacket, " acquired"
        if currentPacket[0:2] != self.BLANK and currentPacket[0:2] != '00' and currentPacket != '1':
            print "Saving scorePacket because ", currentPacket[0:2]
            self.scorePacket = currentPacket
            self.isRunning = True
            print "Scorepacket is : ", self.scorePacket
        if self.oldPacket != currentPacket:
            self.oldPacket = currentPacket
            if self.oldPacket[4] != '0' and self.ishex(self.oldPacket[4]):
                self.checkPCCommand()

    def run(self):
        while True:
            self.capture()





