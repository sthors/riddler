from os.path import expanduser

home = expanduser("~")
# Default configuration for riddler nodes
# Options must be valid python code

wifi_iface = "wlp0s29f7u1"
host = ""
port = 8899
mesh_host = "10.0.0.255"
mesh_port = 8866
power_dev = '/dev/ttyUSB0'
fox_path = '/root/rlncd/build/src/source'
udp_path = '/root/fox/tools/'
rasp_udp_path = "/home/pi/riddler/programs/"
program = '/nc4rasp'
#program = '/dummy_dest'

"""
#When using local host LOCAL_TEST! 
wifi_iface = "wlp0s29f7u1"
host = ""
port = 8899
mesh_host = "localhost"
mesh_port = 8877
power_dev = '/dev/ttyUSB0'
fox_path = '/root/rlncd/build/src/source'
udp_path = '/root/fox/tools/'
rasp_udp_path = home + "/nc4rasp/build/linux/"
program = '/nc4rasp'
"""
