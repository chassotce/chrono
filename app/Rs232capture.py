import serial
import threading
from app import db, app, bareme
from models import Participant, Epreuve
from sqlalchemy.sql import exists
import time


class RS232captureThread(threading.Thread):

    # configure the serial connection
    global ser
    ser = serial.Serial(
        port="/dev/ttyUSB0",
        baudrate=1200,
        parity=serial.PARITY_EVEN,
        stopbits=serial.STOPBITS_ONE,
        bytesize=serial.EIGHTBITS
    )
    global oldPacket
    oldPacket = ""

    isRunning=False

    global hundredNumberRunner, SYNCHRO, BLANK
    hundredNumberRunner = 0
    SYNCHRO = "ff"
    BLANK = "aa"
    penaltyTime = 0

    ser.flush()
    ser.close()
    ser.open()
    print "ser is now open"

    ser.setDTR(True)  #confirms the connection
    ser.setRTS(False)
    print "DTR is set on 1 now"

    global testPacketParcours, testPacketClassement
    testPacketParcours = "aa28000404000000aa1aa2aaaa0000ff"
    testPacketClassement = "2553000404000000aa1aa1aaaa0000ff"

    def getRankPacket(self,rank):
        if rank < 10:
            return "bccb0d0" + str(rank) + "0000000000000000000000ff"
        else:
            return "bccb0d" + str(rank) + "0000000000000000000000ff"

    def getPointPacket(self,point): #Not currently used
        return "000000" "d0" + "0000000000000000000000ff"  #PO at the start


    def getOverlappingPacket(self,overlap): #Not currently used
        return "000000" "bd" + "0000000000000000000000ff"  #dE at the start

    def checkPCCommand(self, pcCommand, currNumber):

        currRunner=db.session.query(Participant).filter(Participant.num_depart == currNumber
                    and Participant.id_epreuve == app.config["CURRENT_EPREUVE_ID"]).first()

        def reset():
            return

        def eliminated():
            currRunner.etat="elimine"
            db.session.commit()

        def gaveUp():
            currRunner.etat="abandon"
            db.session.commit()

        def HC():
            currRunner.hc=True
            db.session.commit()

        def incrTime():
            penaltyTime += 100  #TODO : Check the bareme here or \
            # simply add the points and do it when the classement is established?

        def IncrNumByHundred():
            hundredNumberRunner += 1

        options = {'1': reset,
                   '2': eliminated,
                   '3': gaveUp,
                   '4': HC,
                   '9': incrTime,
                   '11': IncrNumByHundred,
        }
        options[pcCommand]()



    def display(self, currNumber, timePacket):
        ser.setRTS(True)
        print "rts is on true"
        print "Now displaying for runner number : "+str(currNumber)
        app.config["CURRENT_EPREUVE_ID"]=1

        currentCode = db.session.query(Epreuve).filter(Epreuve.id_epreuve == app.config["CURRENT_EPREUVE_ID"])\
            .first().bareme_code

        print currentCode
        res = bareme.Baremes.doBaremes(currentCode)
        infos = next((item for item in res if item["num_depart"] == currNumber), None) #In case more infos are needed

        print infos["rang"]
        rankPacket=self.getRankPacket(infos["rang"]).decode("hex")
        print "RankPacket : "+rankPacket

        time_display = app.config["TMP_AFF_TEMPS"] * 1000
        rank_display = app.config["TMP_AFF_CLASSEMENT"] * 1000

        print "Now displaying time"
        timePacket=timePacket.decode("hex")
        display_time=int(round(time.time() * 1000))+time_display
        while display_time > int(round(time.time() * 1000)): #TODO: Check if that doesn't overflow the PI
            ser.write(timePacket)
        ser.flushOutput()
        print "Flushed, now displaying rank"
        display_time=int(round(time.time() * 1000))+rank_display
        while display_time > int(round(time.time() * 1000)):
            ser.write(rankPacket)
        ser.flushOutput()
        ser.setRTS(False)
        print "displaying done, rts on false"
        return

    def saveRunner(self, currentPacket):

        currentPacket = currentPacket.replace("a", "0")

        currentPen = int(currentPacket[6:8])
        currentTime = int(currentPacket[5]+currentPacket[2:4]+currentPacket[0:2])
        if self.penaltyTime!=0:
            currentTime+=self.penaltyTime
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

            if currentRunner.first().temps_init == None or currentRunner.first().temps_init == 0:
                print "Runner has now a time_init"
                currentRunner.first().points_init=currentPen
                currentRunner.first().temps_init=currentTime
                db.session.commit()

            elif currentRunner.first().temps_barr == None or currentRunner.first().temps_barr == 0:
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
        firstSynchro=ser.read(1).encode("hex")
        while firstSynchro != SYNCHRO:
            firstSynchro=ser.read(1).encode("hex")
        while currentChar != SYNCHRO:
            currentPacket += currentChar
            currentChar = ser.read(1).encode("hex")
        print currentPacket
        print self.isRunning
        if currentPacket[4] != '0':
            print "4 : ",currentPacket[4],", 22 : ", currentPacket[22],", 19 : ", currentPacket[19]
            self.checkPCCommand(currentPacket[4], int(currentPacket[22] + currentPacket[19]))
        if oldPacket != currentPacket:
            global oldPacket
            oldPacket = currentPacket
            if currentPacket[0] == BLANK[0]:
                self.isRunning=True
            else:
                if self.isRunning==True:
                    self.saveRunner(currentPacket)
                    self.display(int(currentPacket[21] + currentPacket[18]) + 100 * hundredNumberRunner, currentPacket)
                    isRunning=False

    def run(self):
         while True:
            self.capture()
        #ser.flush()
        #ser.close()
        #exit()




