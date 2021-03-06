#!/usr/bin/env python3

""" A simple continuous receiver class. """

# Copyright 2015 Mayer Analytics Ltd.
#
# This file is part of pySX127x.
#
# pySX127x is free software: you can redistribute it and/or modify it under the terms of the GNU Affero General Public
# License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later
# version.
#
# pySX127x is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied
# warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Affero General Public License for more
# details.
#
# You can be released from the requirements of the license by obtaining a commercial license. Such a license is
# mandatory as soon as you develop commercial activities involving pySX127x without disclosing the source code of your
# own applications, or shipping pySX127x with a closed source product.
#
# You should have received a copy of the GNU General Public License along with pySX127.  If not, see
# <http://www.gnu.org/licenses/>.


from time import sleep
from SX127x.LoRa import *
from SX127x.LoRaArgumentParser import LoRaArgumentParser
from SX127x.board_config import BOARD
import sqlite3
import datetime
import paho.mqtt.publish as publish



# SQLite DB Name
DB_Name =  "/home/pi/FYP/agristick.db"

BOARD.setup()
parser = LoRaArgumentParser("Continous LoRa receiver.")

#===============================================================
# Database Manager Class

class DatabaseManager():
        def __init__(self):
                self.conn = sqlite3.connect(DB_Name)
                self.conn.execute('pragma foreign_keys = on')
                #self.conn.execute('pragma journal_mode = wal;')
                self.conn.commit()
                self.cur = self.conn.cursor()

        def add_del_update_db_record(self, sql_query, args=()):
                self.cur.execute(sql_query, args)
                self.conn.commit()
                return

        def __del__(self):
                self.cur.close()



#===============================================================

class LoRaRcvCont(LoRa):
    def __init__(self, verbose=False):
        super(LoRaRcvCont, self).__init__(verbose)
        self.set_mode(MODE.SLEEP)
        self.set_dio_mapping([0] * 6)

    def on_rx_done(self):
        BOARD.led_on()
        #print("\nRxDone")
        self.clear_irq_flags(RxDone=1)
        payload = self.read_payload(nocheck=True)
        payload = payload[:-1]

        d = datetime.datetime.now()
        d = str(d)
        mystring = ""
        for char in payload:
                mystring = mystring + chr(char)
        #print (mystring)
        soil_temp = mystring[0:7]
        soil_moist = mystring[7:10]
        atmp_temp = mystring[10:17]
        atmp_hum = mystring[17:24]
        print("datetime: " + d)
        print("Soil Temperature: " + soil_temp)
        print("Soil Moisture: " + soil_moist)
        print("Atmospheric Temperature: " + atmp_temp)
        print("Atmospheric Humidity: " + atmp_hum)
        stringformqtt = d+','+soil_temp+','+soil_moist+','+atmp_temp+','+atmp_hum
        print(stringformqtt)
        #---------------------------------------------------------------------------------------------------------

        dbObj = DatabaseManager()

        dbObj.add_del_update_db_record("insert into sendata (date_time,soil_temp,soil_moist,atmp_temp,atmp_hum) values (?,?,?,?,?)",[d,float(soil_temp),int(soil_moist)$
        del dbObj
        print ("Inserted Data into SENSOR DATA Database.")
       # publish.single("agristick1",str(stringformqtt),hostname="13.232.96.33",auth = {'username':"ubuntu", 'password':"ceglaeee"})
        #print("sent to cloud")
        #---------------------------------------------------------------------------------------------------------
        self.set_mode(MODE.SLEEP)
        self.reset_ptr_rx()
        BOARD.led_off()
        self.set_mode(MODE.RXCONT)

    def on_tx_done(self):
        print("\nTxDone")
        print(self.get_irq_flags())

    def on_cad_done(self):
        print("\non_CadDone")
        print(self.get_irq_flags())

    def on_rx_timeout(self):
        print("\non_RxTimeout")
        print(self.get_irq_flags())

    def on_valid_header(self):
        print("\non_ValidHeader")
        print(self.get_irq_flags())

    def on_payload_crc_error(self):
        print("\non_PayloadCrcError")
        print(self.get_irq_flags())

    def on_fhss_change_channel(self):
        print("\non_FhssChangeChannel")
        print(self.get_irq_flags())

    def start(self):
        self.reset_ptr_rx()
        self.set_mode(MODE.RXCONT)
        while True:
            sleep(.5)
            rssi_value = self.get_rssi_value()
            status = self.get_modem_status()
            sys.stdout.flush()
            sys.stdout.write("\r%d %d %d\n" % (rssi_value, status['rx_ongoing'], status['modem_clear']))


lora = LoRaRcvCont(verbose=False)
args = parser.parse_args(lora)

lora.set_mode(MODE.STDBY)
lora.set_pa_config(pa_select=1)
lora.set_freq(433)
lora.set_bw(BW.BW125)
lora.set_spreading_factor(7)
lora.set_rx_crc(True)
lora.set_coding_rate(CODING_RATE.CR4_5)
#lora.set_pa_config(max_power=0, output_power=0)
#lora.set_lna_gain(GAIN.G1)
#lora.set_implicit_header_mode(False)
#lora.set_low_data_rate_optim(True)
#lora.set_pa_ramp(PA_RAMP.RAMP_50_us)
#lora.set_agc_auto_on(True)

#print(lora)
assert(lora.get_agc_auto_on() == 1)

#try: input("Press enter to start...")
#except: pass

try:
    lora.start()
except KeyboardInterrupt:
    sys.stdout.flush()
    print("")
    sys.stderr.write("KeyboardInterrupt\n")
finally:
    sys.stdout.flush()
    print("")
    lora.set_mode(MODE.SLEEP)
    print(lora)
    BOARD.teardown()
