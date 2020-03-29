from pynput.mouse import Button, Controller
from datetime import datetime
import pexpect
import time
import re
import random


class BluetoothCTLError(Exception):
    """ Exception raised when failing to start process"""
    pass


class BluetoothCTL:

    def __init__(self):
        self.MAC = "E0:DC:FF:05:AE:2D"
        self.command = "(sudo btmgmt find | grep 'E0:DC:FF:05:AE:2D') &>> bt_logs.txt"
        self.btctl = pexpect.spawn("bash", echo=False, encoding="utf-8", maxread=1)
        self.RSSI = None
        self.last_log_count = None
        self.state = True
        self.mouse = Controller()

    def run_command(self, command=None, pause=0, returnOutput=False):
        """Run command against bash"""
        if command is None:
            command = self.command

        self.btctl.send("{}\n".format(command))
        if returnOutput:
            self.btctl.expect("\r\n", timeout=None)
            return self.btctl.before.split("$\x1b[00m ")[-1]

        time.sleep(pause)
        # import pdb;pdb.set_trace()

    def parse_device_info(self, info_string):
        """Find latest device RSSI"""
        # import pdb; pdb.set_trace()
        rssi = None
        try:
            rssi_info = re.search(r"(-\d+)", info_string)
            rssi = rssi_info.group(0)
        except:
            pass
        finally:
            return rssi

    def shutdown_screen(self, timeout=10):
        """Shut down screen for power saving"""
        # import pdb; pdb.set_trace()
        if not self.state:
            return
        time.sleep(timeout)
        print('[{} - LOG] Mirror will shut down, no one nearby'.format(datetime.now()))
        commands = [
                "xset dpms {} {} {}".format(timeout, timeout, timeout),
                "xset s {}".format(timeout)
        ]
        for command in commands:
            self.run_command(command)
            print('[{} - LOG] running command: {}'.format(datetime.now(), command))
        self.state = False


    def powerup_screen(self, timeout=0):
        """Power up screen, the world needs it's hero"""
        self.simulate_input()
        if self.state:
            return

        time.sleep(timeout)
        print('[{} - LOG] Mirror will wake up, someone needs it!'.format(datetime.now()))
        # simulate mouse input
        # self.simulate_input()
        commands = [
            "xset dpms 300 300 300",
            "xset s 300",
        ]
        for command in commands:
            self.run_command(command)
            print('[{} - LOG] running command: {}'.format(datetime.now(), command))

        self.state=True

    def simulate_input(self):
        numbers = list( range(-150, -1) ) + list( range(1, 150) )
        x = random.choice(numbers)
        y = random.choice(numbers)
        print("[{} - LOG] simulating input. x: {}, y: {}".format(datetime.now(), x, y))
        self.mouse.move(x, y)

    def calculate_proximity(self, rssi):
        """Calculate proximity of device"""
        if rssi is None:
            return
        rssi = int(rssi)
        RSSI = self.RSSI
        if RSSI is None:
            RSSI = -2000
        # if self.RSSI == None:
            # print('[LOG] no one is home, shutting down')
            # self.shutdown_screen()
        if rssi < 0:
            if rssi > -70:
                if RSSI - 5 > rssi:
                    # Phone bearing human is going away! :(
                    print('human going away')
                    self.shutdown_screen(60)
                elif RSSI - 5 < rssi:
                    # Phone bearing human is coming closer! :)
                    print('coming closer!')
                    self.powerup_screen()
                else:
                    # Keep going, keep up that mirror!
                    print("[{} - LOG] keeping up!". format(datetime.now()))
                    self.simulate_input()
                    
            if rssi < -75:
                # Human is too far away to use me, gonna sleep (zzz)
                self.shutdown_screen()
        self.RSSI = rssi
        print("[{} - LOG] last RSSI was {}".format(datetime.now(), self.RSSI))

    def check_file_len(self):
        length = self.run_command('wc -l < bt_logs.txt',returnOutput=True)
        return int(length)

    def start_scan(self):
        """Start bluetooth scanning"""
    
        try:
            self.run_command()
            actual_file_len = self.check_file_len()
            
            if actual_file_len == self.last_log_count:
                print('[{} - LOG] no new connections detected, waiting for BT signal'.format(datetime.now()))
                return 
            with open("bt_logs.txt") as f_read:
                if actual_file_len != 0:
                    most_recent = f_read.readlines()[-1]
                    print('[{} - LOG] new log: {}'.format(datetime.now(), most_recent.strip()))
                    #    f_read.close()
                    info = self.parse_device_info(most_recent)
                    self.calculate_proximity(info)
        
                # return info
        except BluetoothCTLError:

            print(e)
            return None

    def stop_scan(self):
        """Stop bluetooth scanning"""
        pass

    
if __name__ == "__main__":

    print("[{} - LOG] Initializing BluetoothRSSIManager ...".format(datetime.now()))
    btm = BluetoothCTL()
    btm.last_log_count = btm.check_file_len() 
    print('[{} - LOG] Last log count: {}'.format(datetime.now(), btm.last_log_count))
    btm.run_command("xset s 300")
    btm.run_command("xset dpms 300 300 300")
    print("[{} - LOG] Ready!".format(datetime.now()))
    while True:
        btm.start_scan()
        btm.last_log_count = btm.check_file_len()
        time.sleep(15)


