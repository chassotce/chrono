import serial
import threading
from app import db, app, bareme
from models import Participant, Epreuve
from sqlalchemy.sql import exists
import time


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

    global hundredNumberRunner, SYNCHRO, BLANK
    hundredNumberRunner = 0
    SYNCHRO = "ff"
    BLANK = "aa"
    penaltyTime = 0

    #ser.open()
    #ser.setRTS(True) TO USE LATER

    #ser.setDTR(True)  #confirms the connection
    print "DTR is set on 1 now"

    global testPacketParcours, testPacketClassement
    testPacketParcours = "aa28000404000000aa1aa2aaaa0000ff"
    testPacketClassement = "2553000404000000aa1aa1aaaa0000ff"

    def __init__(self):
        threading.Thread.__init__(self)

    def getRankPacket(self,rank):
        if rank < 10:
            return "bccb0d0" + str(rank) + "0000000000000000000000ff"
        else:
            return "bccb0d" + str(rank) + "0000000000000000000000ff"

    def getPointPacket(self,point):
        return "000000" "d0" + "0000000000000000000000ff"  #PO at the start


    def getOverlappingPacket(self,overlap):
        return "000000" "bd" + "0000000000000000000000ff"  #dE at the start

    def checkPCCommand(pcCommand, currNumber):

        currRunner=db.session.query(Participant).filter(Participant.num_depart == currNumber
                    and Participant.id_epreuve == app.config["CURRENT_EPREUVE_ID"]).first()

        options = {2: "eliminated",
                   3: "gaveUp",
                   4: "HC",
                   9: "incrTime",
                   11: "IncrNumByHundred",
        }

        options[pcCommand]()

        def eliminated():
            currRunner.etat="elimine"
            db.commit()

        def gaveUp():
            currRunner.etat="abandon"
            db.commit()

        def HC():
            currRunner.hc=True
            db.commit()

        def incrTime():
            penaltyTime += 100  #Bareme C, bareme A adds points

        def IncrNumByHundred():
            hundredNumberRunner += 1

    def display(self, currNumber):
        print "Now displaying with number : "+str(currNumber)
        app.config["CURRENT_EPREUVE_ID"]=1
        currentCode = db.session.query(Epreuve).filter(Epreuve.id_epreuve == app.config["CURRENT_EPREUVE_ID"])\
            .first().bareme_code
        print currentCode
        res = bareme.Baremes.doBaremes(currentCode)
        infos = next((item for item in res if item["num_depart"] == currNumber), None)

        print infos["rang"]
        rankPacket=self.getRankPacket(infos["rang"])
        print "RankPacket : "+rankPacket

        print "temps_init : "+str((infos["temps_init"]))

        time_display = app.config["TMP_AFF_TEMPS"] * 1000
        rank_display = app.config["TMP_AFF_CLASSEMENT"] * 1000

        #TODO : GetTime dans le bon format, verifier la boucle suivante, tester avec le chrono tout ca

        display_time=int(round(time.time() * 1000))+time_display
        while display_time > int(round(time.time() * 1000)): #Seems dubious at most
            "In the loop, display_time : "+str(display_time)
        return 0

    def saveRunner(self, currentPacket):

        currentPacket = currentPacket.replace("a", "0")

        currentPen = int(currentPacket[6:8])
        currentTime = int(currentPacket[0:4]) + self.penaltyTime  #TODO : deal with the fifth number (also seconds)
        #if currentTime < int(app.config["TMP_CHARGE_CHRONO"])*1000:
          #  return
        currentNumber = int(currentPacket[21] + currentPacket[18]) + 100 * hundredNumberRunner

        print "Current Number : {0} , current time : {1} , current penalties : {2}".format(str(currentNumber),
                                                                                           str(currentTime),
                                                                                           str(currentPen))

        currentRunner=db.session.query(Participant).filter(Participant.num_depart == currentNumber
                    and Participant.id_epreuve == app.config["CURRENT_EPREUVE_ID"])

        print db.session.query(currentRunner.exists()).all()
        if "True" in str(db.session.query(currentRunner.exists()).all()):
            print "Runner already in db"

            if currentRunner.first().temps_init == None: #No temps_init for an object Query
                print "Runner has now a time_init"
                currentRunner.first().points_init=currentPen
                currentRunner.first().temps_init=currentTime
                db.session.commit()

            elif currentRunner.first().temps_barr == None:
                print "Runner has now a time_barr"
                currentRunner.first().points_barr=currentPen
                currentRunner.first().temps_barr=currentTime
                db.session.commit()

            else:
                print "Runner has now a time_barr2"
                currentRunner.first().points_barr2=currentPen
                currentRunner.first().temps_barr2=currentTime
                db.session.commit()

        else:
            print "Runner not in db, creating him/her"
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
            else:
                self.display(int(currentPacket[21] + currentPacket[18]) + 100 * hundredNumberRunner)

    def run(self):
       # self.saveRunner(testPacketParcours)
        self.display(21)
        print "testPacketClassement was handled"
        # while True:
        # self.capture()
        #ser.flush()
        #ser.close()
        #exit()




