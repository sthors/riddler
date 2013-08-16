import os
import threading
import subprocess
import time
import re
import riddler_interface as interface

class client(threading.Thread):
    def __init__(self, controller, dest_node, run_info, args):
        super(client, self).__init__(None)
        self.controller = controller
        self.dest_node = dest_node
        self.run_info = run_info
        self.args = args
        self.running = False
        self.ping_p = None
        self.timer = threading.Timer(run_info['test_time']*2, self.kill_client)
	
	#TASK! Make run fit to the purpose of the 
    def run(self):
        print ("   real run")#CHANGE!
        if self.run_info['profile'] in ( 'udp_rates', 'power_meas','udp_ratios','hold_times','tcp_algos','tcp_windows','rlnc'):
            self.python_client()
        elif self.run_info['profile'] in ('rasp_rank'):
            self.rasp_client()
            
    def python_client(self):
		#The command given to c++ program
        h = self.dest_node['host']
        t = str(self.run_info['test_time'])
        l = str(self.run_info['iperf_len'])
        r = str(self.run_info['rate'])
        
        p = os.path.dirname(self.args.udp_path) + "/udp_client.py"
        
        cmd = [p, h, l, r, t, "1"]

        print("  Starting client: {}".format(cmd))
        self.timer.start()
        self.p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, close_fds=True)
        self.running = True
        self.p.wait()
        self.running = False
        
        (stdout, stderr) = self.p.communicate()
        if stderr:
            self.report_error("udp_client.py error: {}".format(stderr))
            return
        elif not stdout:
            self.report_error("No output from command {0}".format(" ".join(cmd)))
            return

        result = {}
        for line in stdout.splitlines():
            key,val = line.split(": ")
            result[key] = float(val)

        if result:
            self.report_result(result)
        else:
            self.report_error("Missing result")

    def rasp_client(self): #CHANGE!
        #The command given to the c++ program
        print "   rasp_client node_tester"
        
        #TASK! RASP! CHANGE! Hardcode hack to make it work
        
        h = "-host=" +  str(self.dest_node['host'])
        f = "-field=" + "binary"
        i = "-iteration=" + '100' #FIX!
        s = "-symbols=" + str(self.run_info['gen_size']) #FIX!
        l = "-symbol_size=" + str(self.run_info['packet_size'])
        r = "-rate=" + '1000' #str(self.run_info['rate'])
        g = "-port=" + str(self.args.mesh_port)
        t = "-type=" + 'source'
        #FIX! symbol_siz is missing
        
        p = os.path.dirname(self.args.rasp_udp_path) + "/rasp"
        
        cmd = [p, h, f, i, s, l, r, g, t]
        print cmd
        
        self.timer.start()
        self.p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, close_fds=True)
        self.running = True
        self.p.wait()
        self.running = False
        
        
    
    # Brutally kill a running subprocesses
    def kill_client(self):
        # Make sure even have a running subprocess
        if not self.running:
            return

        try:
            # Ask politely first
            print("  Terminating client (pid {0})".format(self.p.pid))
            self.p.terminate()

            # Ask again, if necessary
            if not self.p.poll():
                self.p.terminate()

            # No more patience, kill the damn thing
            if not self.p.poll():
                self.p.kill()
        except OSError as e:
            print("  Killing client failed: {0}".format(e))

        # We are done
        self.running = False

    # Send back a result to the controller
    def report_result(self, result):
        print("  Reporting result")
        obj = interface.node(interface.RUN_RESULT, result=result)
        self.controller.report(obj)

    # Send back an error to the controller
    def report_error(self, error):
        #print error
        print("  Reporting error")
        obj = interface.node(interface.RUN_ERROR, error=error)
        self.controller.report(obj)


class server(threading.Thread):
    def __init__(self, controller, args, run_info):
        super(server, self).__init__(None)
        self.controller = controller
        self.args = args
        self.run_info = run_info
        self.protocol = run_info['protocol']
        self.tcp_window = run_info['tcp_window']
        self.iperf_len = run_info['iperf_len']
        self.running = False
        self.start()

    def run(self):#TASK! Need to be corrected to mabe two functions
        if self.run_info['profile'] in ( 'udp_rates', 'power_meas','udp_ratios','hold_times','tcp_algos','tcp_windows','rlnc'):
            print "   python server" #CHANGE!
            self.python_server()
        elif self.run_info['profile'] in ('rasp_rank'):
            print "   rasp_server"
            self.rasp_server()
            
    def rasp_server(self):
        #l = str(self.iperf_len)
        p = os.path.dirname(self.args.rasp_udp_path) + "/rasp"
        
        #h = "-host=" + str(self.dest_node['host'])
        f = "-field=" + "binary"
        i = "-iteration=" + '100' #FIX!
        s = "-symbols=" + str(self.run_info['gen_size']) #FIX!
        l = "-symbol_size=" + str(self.run_info['packet_size'])
        r = "-rate=" + '1000' # str(self.run_info['rate'])
        g = "-port=" + str(self.args.mesh_port)
        t = "-type=" + 'receiver'
        
        self.cmd = [p, f, i, s, l, r, g, t]
        print self.cmd
        
        print("  Starting server: {}".format(self.cmd))

        self.p = subprocess.Popen(self.cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, close_fds=True)
        self.running = True
        self.p.wait()
        self.running = False
        
        (stdout,stderr) = self.p.communicate()

        if stderr:
            obj = interface.node(interface.RUN_ERROR, error=stderr)
            self.controller.report(obj)
            return
        elif not stdout:
            obj = interface.node(interface.RUN_ERROR, error="no server result")
            self.controller.report(obj)
            return

        result = {}
        for line in stdout.splitlines():
            key,val = line.split(":")
            result[key] = float(val)

        if result:
            obj = interface.node(interface.RUN_RESULT, result=result)
            self.controller.report(obj)
        else:
            obj = interface.node(interface.RUN_ERROR, error="empty server result")
            self.controller.report(obj)
        
        
    def python_server(self):
        l = str(self.iperf_len)
        p = os.path.dirname(self.args.udp_path) + "/udp_server.py"
        self.cmd = [p, l, "1"]

        print("  Starting server: {}".format(self.cmd))
        self.p = subprocess.Popen(self.cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, close_fds=True)
        self.running = True
        self.p.wait()
        self.running = False

        (stdout,stderr) = self.p.communicate()

        if stderr:
            obj = interface.node(interface.RUN_ERROR, error=stderr)
            self.controller.report(obj)
            return
        elif not stdout:
            obj = interface.node(interface.RUN_ERROR, error="no server result")
            self.controller.report(obj)
            return

        result = {}
        for line in stdout.splitlines():
            key,val = line.split(": ")
            result[key] = float(val)

        if result:
            obj = interface.node(interface.RUN_RESULT, result=result)
            self.controller.report(obj)
        else:
            obj = interface.node(interface.RUN_ERROR, error="empty server result")
            self.controller.report(obj)


    # Kill a running iperf server
    def kill(self):
        # Check if process is running at all
        if not self.running:
            return

        try:
            # Politely ask server to quit
            print("  Terminating server (pid {0})".format(self.p.pid))
            self.p.terminate()

            # Ask again if necessary
            if not self.p.poll():
                self.p.terminate()

            # No more patience, kill the damn thing
            if not self.p.poll():
                self.p.kill()
        except OSError as e:
            print("  Killing server failed: {0}".format(e))

        # We are done here
        self.running = False
