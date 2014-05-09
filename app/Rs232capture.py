import serial
import threading
from app import db, app, bareme
from models import Participant, Epreuve
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
            isConnected = False
            time.sleep(5)

    oldPacket = ""
    currentNumber = 0
    scorePacket = ""
    isRunning = False
    currentEtat = "undef"
    hc = False

    SYNCHRO = "ff"
    BLANK = "aa"

    ser.flush()
    ser.close()
    ser.open()

    if ser.isOpen():
        app.config["CHRONO_CONNECT"] = True

    ser.setDTR(True)  #confirms the connection
    ser.setRTS(False)


    def ishex(self, val):
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
        checkingRunner = db.session.query(Participant).filter_by(num_depart =self.currentNumber \
            ,id_epreuve =app.config["CURRENT_EPREUVE_ID"])
        if "True" in str(db.session.query(checkingRunner.exists()).all()):
            return
        else:
            runnerToAdd = Participant(
                num_depart=self.currentNumber, id_epreuve=app.config["CURRENT_EPREUVE_ID"])
            db.session.add(runnerToAdd)
            db.session.commit()
            return
        return


    def getRunner(self):
        return db.session.query(Participant).filter_by(num_depart =self.currentNumber \
            ,id_epreuve =app.config["CURRENT_EPREUVE_ID"]).first()

    def checkPCCommand(self):

        def nothing():
            return

        def reset():
            if self.scorePacket is not "" and self.oldPacket[0] != self.BLANK[0] and self.isRunning:
                self.saveRunner()
                if app.config["SEND_AFF"]:
                    self.display()
            return

        def eliminated():
            self.currentEtat = "elimine"
            return

        def gaveUp():
            self.currentEtat = "abandon"
            return

        def HC():
            self.hc = True
            return

        def changeNumber():
            if self.oldPacket[6:8].isdigit() and int(self.oldPacket[6:8]) is not 0:
                self.currentNumber = int(self.oldPacket[6:8])
            return

        def IncrNumByHundred():
            self.currentNumber += 100
            time.sleep(0.8)
            self.ser.flushInput()
            return

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
        try:
            if self.scorePacket is '000000000000000000000000000000':
                return
            self.ser.setRTS(True)

            currentCode = db.session.query(Epreuve).filter_by(id_epreuve = app.config["CURRENT_EPREUVE_ID"]) \
                .first().bareme_code
            res = bareme.Baremes.doBaremes(currentCode,app.config["CURRENT_EPREUVE_ID"])
            infos = next((item for item in res if item["num_depart"] == self.currentNumber),
                         None)  #In case more infos are needed
            if infos is not None:
                rankPacket = self.getRankPacket(infos["rang"])
                rankPacket = rankPacket.decode("hex")

                time_display = app.config["TMP_AFF_TEMPS"] * 1000
                rank_display = app.config["TMP_AFF_CLASSEMENT"] * 1000

                timePacket = (self.scorePacket + "ff")
                timePacket = timePacket.decode("hex")
                display_time = int(round(time.time() * 1000)) + time_display

                while display_time > int(round(time.time() * 1000)):  #TODO: Check if that fits the planned time
                    self.ser.write(timePacket)

                display_time = int(round(time.time() * 1000)) + rank_display
                while display_time > int(round(time.time() * 1000)):
                    self.ser.write(rankPacket)
            self.ser.setRTS(False)
            self.scorePacket = ""
            return
        except:
            self.ser.setRTS(False)
            return

    def saveRunner(self):

        currentPacket = self.scorePacket.replace("a", "0")

        currentPen = int(currentPacket[6:8])
        currentTime = int(currentPacket[5] + currentPacket[2:4] + currentPacket[0:2])
        if currentTime < int(app.config["TMP_CHARGE_CHRONO"]) * 100:
            self.scorePacket= '000000000000000000000000000000'
            return

        self.checkRunner()
        currentRunner = self.getRunner()
        if currentRunner.temps_init is None or currentRunner.temps_init is 0:
            currentRunner.points_init = currentPen
            currentRunner.temps_init = currentTime
            currentRunner.etat_init = self.currentEtat

        elif currentRunner.temps_barr is None or currentRunner.temps_barr is 0:
            currentRunner.points_barr = currentPen
            currentRunner.temps_barr = currentTime
            currentRunner.etat_barr = self.currentEtat
        else:
            currentRunner.points_barr2 = currentPen
            currentRunner.temps_barr2 = currentTime
            currentRunner.etat_barr2 = self.currentEtat
        if not app.config["SEND_AFF"]:
            self.isRunning = False
        if currentRunner.hc is None or currentRunner.hc is not True:
            currentRunner.hc = self.hc
        db.session.commit()
        self.currentEtat = "undef"
        self.hc = False
        return

    def capture(self):
        currentPacket = ""
        currentChar = ""
        firstSynchro = self.ser.read(1).encode("hex")
        while firstSynchro != self.SYNCHRO:
            firstSynchro = self.ser.read(1).encode("hex")
        while currentChar != self.SYNCHRO:
            currentPacket += currentChar
            currentChar = self.ser.read(1).encode("hex")
        if currentPacket[0:2] != self.BLANK and currentPacket[0:2] != '00' and currentPacket != '1':
            self.scorePacket = currentPacket
            self.isRunning = True
        if self.oldPacket != currentPacket:
            self.oldPacket = currentPacket
            if self.oldPacket[4] != '0' and self.ishex(self.oldPacket[4]):
                self.checkPCCommand()
        return

    def run(self):
        while True:
            while self.ser.isOpen():
                self.capture()





