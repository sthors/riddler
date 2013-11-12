import SocketServer
import socket
import threading
import time
import riddler_interface as interface
import node_tester as tester
#import node_sampler as sampler
import node_setup as setup
import subprocess
import os.path
report_sleep = 1 #TIME!

class server:
    def __init__(self, args):
        self.args = args

    def create(self):
        self.server = SocketServer.TCPServer((self.args.host, self.args.port), tcp_handler, bind_and_activate=False) #make a server
        self.server.allow_reuse_address = True
        self.server.timeout = 1 #TIME!
        self.server.running = True
        self.server.args = self.args
        self.server.server_bind() #binds to desired address
        self.server.server_activate() #starting server and listen

    def serve(self):
        print("# Waiting for controller connection") #The first line printed out
        while self.server.running:
            try:
                self.server.handle_request() #handles the requests
            except socket.error as e:
                print(e)
                continue
            except KeyboardInterrupt:
                print("Quit")
                return

    def stop(self):
        if self.server:
            self.server.running = False

class tcp_handler(SocketServer.BaseRequestHandler): #request handler class with BaseRequestHandler as subclass
    # Prepare objects upon a new connection
    def setup(self):
        print("  Connected to controller: {}".format(self.client_address)) #when the connection is made
        self.end = threading.Event()
        self.tester_clients = []
        self.tester_server = None
        self.run_info = None
        self.lock = threading.Lock()
        #self.sampler = sampler.sampler(self, self.server.args)
        self.setup = setup.setup(self.server.args)
        self.send_node_info()

    # Stop running threads before connection closes
    def finish(self):
        print("# Disconnect from controller")
        for client in self.tester_clients:
            print("  Killing client")
            client.stop()
            client.kill_client()
            #client.kill_ping(force=True)
            if client.is_alive():
                client.join()

        if self.tester_server:
            print("  Killing server")
            self.tester_server.kill()
            if self.tester_server.is_alive():
                self.tester_server.join()

        try:
            del self.setup
        except AttributeError:
            pass

        #if self.sampler:
        #    print("  Killing sampler")
        #    self.sampler.stop()
        #    if self.sampler.is_alive():
        #        self.sampler.join(1)
        #    if self.sampler.is_alive():
        #        print("  Sampler wouldn't die")

        print("  Closing connection")

    # Read data from controller
    def handle(self): #This overrides the handle method
        while not self.end.is_set():
            try:
                obj = interface.recv(self.request)
                if not obj:
                    break
                self.handle_cmd(obj) #handles the command send to the server
                #print ("# Handle_cmd end") #DEBUG!
            except socket.error as e:
                print("Connection to controller lost: {0}".format(e))
                break
            except KeyboardInterrupt:
                self.server.running = False
                break
        print("# Handle end")

    # Handle commands/data from controller
    def handle_cmd(self, obj): #Three commands during a test
        if obj.cmd is interface.PREPARE_RUN: #prepares the run
            self.prepare_run(obj)
        elif obj.cmd is interface.START_RUN: #starts the run
            self.start_run(obj)
        elif obj.cmd is interface.FINISH_RUN: #finishes the run
            self.finish_run(obj)
            print("# Finished run")
        else:
            print("Received unknown command: {0}".format(obj.cmd))

    # Prepare this node for a new test run
    def prepare_run(self, obj):
        print("# Prepare run")
        self.run_info = obj.run_info #run info sendt from riddler controller

        # Apply received configurations
        if not self.setup.apply_setup(obj.run_info):
            self.report(interface.node(interface.PREPARE_ERROR, error=self.setup.error)) # Had a setup error
        # Inform the sampler about the new run
        #if not self.sampler.set_run_info(obj.run_info):
        #    print(self.sampler.error)
        #    self.report(interface.node(interface.PREPARE_ERROR, error=self.sampler.error))

        # (Re)start iperf server
        if self.tester_server: #Kills any remaining tester servers
            self.tester_server.kill()
        
        
        if self.run_info['role'] == "destination": #if the node is a destination
            self.tester_server = tester.server(self, self.server.args, obj.run_info)
        
        # Wait for previous iperf clients to finish
        for client in self.tester_clients:
            print("#  Waiting for clients to finish")
            client.stop()#INTEREST!

        # Prepare new iperf client threads
        self.tester_clients = []
        for node in obj.dests:
            client = tester.client(self, node, obj.run_info, self.server.args)
            self.tester_clients.append(client)
            if self.run_info['profile'] in ('rasp_rank', 'rasp_symbols_sweep'): #RASP! #ADD_TEST! #NEW_TEST! #only one source is needed
                break

        # Report back to controller that we are ready
        time.sleep(1) #TIME!
        self.report(interface.node(interface.PREPARE_DONE)) #reporting to the controller that the node is ready
        print("# report  PREPARE_DONE") #DEBUG!

    def start_run(self, obj):
        print("# Start run")
        
        #print "profile:",self.run_info['profile']
        if self.run_info and self.run_info['profile'] in ( 'udp_rates', 'power_meas','udp_ratios','hold_times','tcp_algos','tcp_windows','rlnc'): #RASP! NEW_TEST!
            self.send_sample()
        elif self.run_info and self.run_info['profile'] in ('rasp_rank', 'rasp_symbols_sweep'):
            pass
        
        print('# Start clients') #DEBUG! next node_tester.py, client, run
        for client in self.tester_clients:
            client.start()
        
        # If no clients exists, we don't want the controller to
        # wait for us, so we send an empty result immediately.
        
        if self.run_info and self.run_info['profile'] in ( 'udp_rates', 'power_meas','udp_ratios','hold_times','tcp_algos','tcp_windows','rlnc'):
            self.send_dummy_result()
        elif self.run_info and self.run_info['profile'] in ('rasp_rank', 'rasp_symbols_sweep'): #NEW_TEST! Only if source is not returning result
            self.rasp_send_dummy_result()
        
    def send_dummy_result(self): #RASP!
        try:
            if self.run_info['role'] == 'helper':
                #print("  Sending dummy result")
                time.sleep(report_sleep) #TIME!
                obj = interface.node(interface.RUN_RESULT, result=None)
                self.report(obj)
        except AttributeError as e:
            time.sleep(report_sleep) #TIME!
            obj = interface.node(interface.RUN_ERROR, error=e)
            self.report(obj)
            print("  Run error: " + e)
        else:
            print("  Run done")
            
    def rasp_send_dummy_result(self):
        try:
            if self.run_info['role'] == 'source':
                print('# Sending dummy result') #DEBUG!
                time.sleep(report_sleep) #TIME!
                obj = interface.node(interface.RUN_RESULT, result=None)
                self.report(obj)
                print("# report RUN_RESULT") #DEBUG!
        except AttributeError as e:
            time.sleep(report_sleep) #TIME!
            obj = interface.node(interface.RUN_ERROR, error=e)
            self.report(obj)
            print("  Run error: " + e)
        else:
            print("  Run done")
            
    def finish_run(self, obj):
        print("# Finish run")
        
        if self.run_info['profile'] in ( 'udp_rates', 'power_meas','udp_ratios','hold_times','tcp_algos','tcp_windows','rlnc'): #RASP! NEW_TEST!
            self.send_sample(finish=True)
        elif self.run_info['profile'] in ('rasp_rank', 'rasp_symbols_sweep'):
            pass

        if self.run_info and self.run_info['coding'] == 'helper' and not self.setup.check_fox():
            err = interface.node(interface.RUN_ERROR, error="fox failed")
            self.report(err)
            return

        if self.run_info and self.run_info['coding'] == 'nohelper' and self.run_info['role'] != 'helper' and not self.setup.check_fox():
            err = interface.node(interface.RUN_ERROR, error="fox failed")
            self.report(err)
            return
        
        print('# Stop client')    
        for client in self.tester_clients:
            client.stop() #INTEREST!

        # Report back to controller that we are done
        time.sleep(report_sleep) #TIME!
        self.report(interface.node(interface.FINISH_DONE))
        print("# report FINISH_DONE")#DEBUG!

    # Thread safe sender function
    def report(self, obj):
        self.lock.acquire()
        ret = interface.send(self.request, obj)
        self.lock.release()
        if not ret:
            print("# report error") #DEBUG!
            self.end.set()
        return ret

    # Send our own information to the controller
    def send_node_info(self):
        args = self.server.args
        if os.path.exists("/sys/class/net/{}/address".format(args.wifi_iface)):
            mac = open("/sys/class/net/{}/address".format(args.wifi_iface)).read()
        else:
            mac = None
        obj = interface.node(interface.NODE_INFO, mesh_host=args.mesh_host, mesh_port=args.mesh_port, mesh_mac=mac)
        self.report(obj)
        print("# report NODE_INFO")

    def send_sample(self, finish=False):
        try:
            sample = {'timestamp': time.time()}

            # Sample bat stats
            print("  Sample bat stats")
            cmd = ["batctl", "s"]
            p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, close_fds=True)
            p.wait()
            nc,d = p.communicate()

            # Sample iw
            print("  Sample iw")
            cmd = ["iw", "dev", self.server.args.wifi_iface, "station", "dump"]
            p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, close_fds=True)
            p.wait()
            iw,d = p.communicate()

            # Sample cpu
            print("  Sample cpu")
            cpu = open("/proc/stat").read()

            # Sample fox
            if finish:
                fox = self.sample_fox()
            else:
                fox = ""

            print("  Send sample")
            sample = interface.node(interface.SAMPLE, sample=sample, nc=nc, iw=iw, cpu=cpu, fox=fox)
            self.report(sample)
        except Exception as e:
            err = interface.node(interface.SAMPLE_ERROR, error=e)
            self.report(err)

    def sample_fox(self):
        if self.run_info['role'] == 'helper' and self.run_info['coding'] == 'nohelper':
            return ""

        if self.run_info['coding'] in ("loss", "noloss"):
            return ""

        print("  Sample fox")
        cmd = ["{}/counters".format(os.path.dirname(self.server.args.fox_path))]
        p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, close_fds=True)
        p.wait()
        fox,d = p.communicate()

        if d:
            print("Failed to sample fox")
            raise Exception("fox counters returned error")

        return fox
