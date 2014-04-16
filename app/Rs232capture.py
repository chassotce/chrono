__author__ = 'xaxa'

import serial
from app import db
from models import Participant
from sqlalchemy.sql import exists


class RS232capture:
    # configure the serial connection
    global ser
    ser = serial.Serial(
        port='/dev/ttyUSB0',
        baudrate=1200,
        parity=serial.PARITY_EVEN,
        stopbits=serial.STOPBITS_ONE,
        bytesize=serial.EIGHTBITS
    )
    oldPacket = ""
    global penaltyTime
    ser.open()
    #ser.setRTS(True) TO USE LATER

    ser.setDTR(True)  #confirms the connection
    print 'DTR is 1 now'

    #test= '000500bd0000000000000000000000ff'.decode("hex")

    #TODO: Another thread about sending the correct packet to display?
    def getRankFrame(rank):
        if rank < 10:
            frame = 'bccb0d0' + str(rank) + '0000000000000000000000ff'
            return frame.decode("hex")
        else:
            frame = 'bccb0d' + str(rank) + '0000000000000000000000ff'
            return frame.decode("hex")

    def getPointFrame(point):
        frame = '000000' 'd0' + '0000000000000000000000ff'  #PO at the start
        return frame.decode("hex")

    def getOverlappingFrame(overlap):
        frame = '000000' 'bd' + '0000000000000000000000ff'  #dE at the start
        return frame.decode("hex")


    def eliminated():
        db.session.query(Participant).filter_by(num_depart=currNumber).update(
                {}) #Declare the right thing

    def gaveUp():
        db.session.query(Participant).filter_by(num_depart=currNumber).update(
                {}) #Declare the right thing

    def HC():
        db.session.query(Participant).filter_by(num_depart=currNumber).update(
                {}) #Declare the right thing

    def incrTime():
        penaltyTime+=1

    def IncrNumByHundred():
        nothing=0
        #TODO

    def isBarrage():
        nothing=0
        #TODO

    def checkPCCommand(pcCommand, currNumber):
        options = {2: eliminated,
                3: gaveUp,
                4: HC,
                9: incrTime,
                11: IncrNumByHundred,
                12: isBarrage,
        }
        options[pcCommand]()

    def saveRunner(currentPacket):
        currentPen = int(currentPacket[7:8])
        currentTime = int(currentPacket[1:4])  #TODO : deal with the fifth number (also seconds)
        currentNumber = int(currentPacket[22] + currentPacket[19])

        print "Current Number : %s, current time : %s, current penalties : %s", \
            currentNumber, currentTime, currentPen

        #TODO: Check if we don't miss any packet due to the limited performances of the PI
        #TODO: Another thread to deal with the DB during the capture if that's the case

        if (db.session.query(exists().where(Participant.num_depart == currentNumber).scalar())):  #TODO:CORRECT?
            db.session.query(Participant).filter_by(num_depart=currentNumber).update(
                {"points_init": currentPen}, {"temps_init": currentTime})
        else:
            currentRunner = Participant(
                num_depart=currentNumber, points_init=currentPen, temps_init=currentTime)
            db.session.add(currentRunner)
        db.session.commit()
        penaltyTime=0

    def capture(self, oldPacket=None):
        currentPacket = ""
        currentChar = ""
        while currentChar != "ff":
            currentPacket += currentChar
            currentChar = ser.read(1).encode("hex")
        print currentPacket
        if currentPacket[6] != 0:
            self.checkPCCommand(currentPacket[6], int(currentPacket[22] + currentPacket[19]))
        if oldPacket != currentPacket:
            oldPacket = currentPacket
            if "aa" != currentPacket[0:1]:
                self.saveRunner(currentPacket)

    def main(self):
        while 1:
            self.capture()
            #ser.flush()
            #ser.close()
            #exit()

    main()