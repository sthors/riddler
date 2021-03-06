import time
import threading
import riddler_interface as interface
import riddler_plot as plotter

class controller(threading.Thread):
    def __init__(self, args):
        super(controller, self).__init__(None)
        self.name = "   controller   "
        self.args = args
        self.run_info = {}
        self.individual_info = [] #INDIVIDUAL_NODE!

        self.error = False
        self.redo = False
        self.recover_timer = None
        self.end = threading.Event()
        self.pause = threading.Event()
        self.test_num = 0

    # Stop the controller
    def stop(self):
        # Tell thread to stop
        self.end.set()

    def set_pause(self, pause):
        if pause:
            self.pause.clear()
        else:
            self.pause.set()

    # Toggle the pause event to pause tests
    def toggle_pause(self):
        if self.pause.is_set():
            # Pause: on
            self.pause.clear()
            return True
        else:
            # Pause: off
            self.pause.set()
            return False

    # Sleep function that breaks, if controller is stopped
    def sleep(self, secs):
        for i in range(secs):
            time.sleep(1) #TIME!
            if self.end.is_set():
                return True
        return False

    def run(self):
        # Disable pause
        self.pause.set()

        try:
            self.control()
        except KeyboardInterrupt:
            return
    
    def control(self):
        #print("   controller   ")  #DEBUG!
        self.start_time = time.time()
        self.init_ranges()
        self.initial_eta = self.test_time * self.test_count
        profile = self.args.test_profile

        # Select control function based on configured profile
        if profile in ("udp_rates","power_meas"):
            self.test_rates()

        elif profile == "udp_ratios":
            self.test_ratios()

        elif profile == "tcp_algos":
            self.test_tcp_algos()

        elif profile == "tcp_windows":
            self.test_tcp_windows()

        elif profile == "hold_times":
            self.test_hold_times()

        elif profile == "rlnc":
            self.test_rlnc()
            
        elif profile == "rasp_rank": #RASP!
            self.test_rasp_rank()
        
        elif profile == "rasp_symbols_sweep":
            self.test_rasp_symbols_sweep()
            
        elif profile == "rasp_link_quality":
            self.test_link_quality()
        
        else:
            print("Profile '{0}' not supported.".format(profile))
            return

        # Yeah, the test actually completed by itself
        if not self.end.is_set():
            total_time = time.time() - self.start_time
            print("Original ETA was {}".format(self.format_time(self.initial_eta)))
            print("Test completed in {}".format(self.format_time(total_time)))
            
            #TASK! Data processing
            self.data.save_csv()
            df = self.data.load_csv()
            if self.args.plot_enable:
                plot = plotter.plot(df)
                if "rank_plot" in self.args.plot_list: #ADD_PLOT!
                    plot.plot_rank()
                else:
                    print "Error no plots are chosen"
            else:
                print("# Plotting is disabled")
            
    
    #RASP! NEW_TEST! FOR_LOOPS! INDIVIDUAL_NODE!
    #Control function to test rank on rasberry
    def test_link_quality(self):
        for loop in self.loops:
            for field in self.fields:
                num_nodes = list(range(self.number_of_nodes))
                self.individual_info = [['id'],num_nodes]
                symbols = self.args.gen_size
                rate = self.args.rlnc_rates[True]
                linkquality = 'true'
                self.set_run_info(loop=loop, rate=rate, field=field, symbols=symbols, linkquality=linkquality)
                self.execute_run()
                # Quit if we are told to
                if self.end.is_set():
                    return
    
    def test_rasp_symbols_sweep(self):
        for loop in self.loops:
            for field in self.fields: #FIELDS_EXAMPLE!
                for symbols in self.symbols:
                    num_nodes = list(range(self.number_of_nodes)) #INDIVIDUAL_TEST!
                    self.individual_info = [['id'],num_nodes]
                    rate = self.args.rlnc_rates[True]
                    linkquality = 'false'
                    self.set_run_info(loop=loop, rate=rate, field=field, symbols=symbols, linkquality=linkquality)
                    self.execute_run()
                    # Quit if we are told to
                    if self.end.is_set():
                        return
    
    def test_rasp_rank(self):
        for loop in self.loops:
            for field in self.fields:
                #print "field:",field  #DEBUG!
                #print "loop:", loop  #DEBUG!
                num_nodes = list(range(self.number_of_nodes)) #INDIVIDUAL_TEST!
                self.individual_info = [['id'],num_nodes]
                rate = self.args.rlnc_rates[True]
                symbols = self.args.gen_size
                linkquality = 'false'
                self.set_run_info(loop=loop, rate=rate, field=field, symbols=symbols, linkquality=linkquality)
                self.execute_run()
                # Quit if we are told to
                if self.end.is_set():
                    print ("returning from test_rasp_rank")
                    return
        print ("# End of rasp_rank_test")
    
    # Control function to swipe UDP rates
    def test_rates(self):
        hold = self.args.hold_time
        purge = self.args.purge_time

        for loop in self.loops:
            for rate in self.rates:
                for coding in self.codings:
                    self.set_run_info(loop=loop, rate=rate, hold=hold, purge=purge, coding=coding)
                    self.execute_run()
                    # Quit if we are told to
                    if self.end.is_set():
                        return

    # Control function to swipe ratios between
    def test_ratios(self):
        hold = self.args.hold_time
        purge = self.args.purge_time

        for loop in self.loops:
            for rate in self.rates:
                for ratio in self.ratios:
                    for coding in self.codings:
                        self.set_run_info(loop=loop, rate=rate, ratio=ratio, hold=hold, purge=purge, coding=coding)
                        self.execute_run()

                    if self.end.is_set():
                        return

    # Control function to swipe TCP congestion avoidance algorithms
    def test_tcp_algos(self):
        hold = self.args.hold_time
        purge = self.args.purge_time
        window = self.args.tcp_window

        for loop in self.loops:
            for algo in self.args.tcp_algos:
                for coding in self.codings:
                    self.set_run_info(loop=loop, hold=hold, purge=purge, coding=coding, tcp_algo=algo, tcp_window=window)
                    self.execute_run()

                    # Quit if we are told to
                    if self.end.is_set():
                        return

    # Control function to swipe TCP windows sizes
    def test_tcp_windows(self):
        hold = self.args.hold_time
        purge = self.args.purge_time
        tcp_algo = self.args.tcp_algo

        for loop in self.loops:
            for window in self.tcp_windows:
                for coding in self.codings:
                    self.set_run_info(loop=loop, hold=hold, purge=purge, coding=coding, tcp_window=window, tcp_algo=tcp_algo)
                    self.execute_run()

                    # Quit if we are told to
                    if self.end.is_set():
                        return

    # Control function to swipe different hold times
    def test_hold_times(self):
        purge = self.args.purge_time

        for loop in self.loops:
            for hold in self.hold_times:
                self.set_run_info(loop=loop, hold=hold, purge=purge, coding=True)
                self.execute_run()

                # Quit if we are told to
                if self.end.is_set():
                    return

    def test_rlnc(self):
        for loop in self.loops:
            for error in self.args.errors:
                for ack in self.args.ack_timeout:
                    for req in self.args.req_timeout:
                        for encoder in self.args.encoders:
                            for coding in self.codings:
                                rate = self.args.rlnc_rates[coding]
                                self.set_run_info(loop=loop, coding=coding, errors=error, ack=ack, req=req, rate=rate, encoders=encoder)
                                self.execute_run()

                    if self.end.is_set():
                        return

    # Control the state of each node and execute a single test run
    def execute_run(self):
        print("# Executing run")  #DEBUG!
        while not self.end.is_set():
            time.sleep(1)
            # Make time stamp for use in ETA
            
            if self.redo:
                pass #Maybe build in some 
            
            start = time.time()

            # Check if we should pause and rerun
            #print("waiting.. one") #DEBUG!
            self.wait_pause()
            #print("wait over") #DEBUG!
            self.prepare_run() #INDIVIDUAL_NODE!
            self.test_num += 1

            # Let the network settle before next test
            self.sleep(self.args.test_sleep)

            # Wait for run to finish and check the result
            self.print_run_info(self.run_info)
            self.exec_node()

            # Let the nodes clean up and save data
            self.finish_run()
            #print("# Waiting...") #DEBUG!
            # Check if we should pause and rerun
            self.wait_pause()
            #print("#Waiting is done") #DEBUG!
            # Decide on the next action
            if self.end.is_set(): #DEBUG_HYPO!
                # Quit
                print("# Ending test")
                return

            elif not self.error:
                # We always discard the first result after an error
                if self.redo:
                    #print("Discarding result because of previous error")
                    self.redo = False
                    #continue
                
                if self.run_info['profile'] in ( 'udp_rates', 'power_meas','udp_ratios','hold_times','tcp_algos','tcp_windows','rlnc'): #RASP! NEW_TEST!
                    if not self.save_samples():
                        print("Samples failed; redoing test")
                        continue
                elif self.run_info['profile'] in ('rasp_rank', 'rasp_symbols_sweep','rasp_link_quality'): #ADD_TEST!
                    pass
                    """
                    if not self.save_samples():
                        print("Samples failed; redoing test")
                    """
                # Successful test
                self.save_results()

                # Update test count
                self.test_count -= 1
                self.test_time = int(time.time() - start)
                break

            else:
                # Test failed, run it again
                print("Take a chill pill:) We experienced an error and the test will return in a moment...")
                #time.sleep(120) #CHANGE!
                time.sleep(60) #CHANGE!
                print("Redoing test")
                self.redo = True

    # Check if pause is requested and pause if so
    def wait_pause(self):
        # Check the user setting
        if self.pause.is_set():
            #print("# pause is set") #DEBUG!
            # Nope, we don't pause
            return False

        # Invalidate current run
        print("Error from pause")
        self.error = True

        # Pause until told otherwise
        print("Pausing")
        while not self.end.is_set():
            if self.pause.wait(.1):
                print("Continuing")
                break

    def restart_timer(self):
        # Start timer to recover from broken code!
        if self.recover_timer:
            self.recover_timer.cancel()
        self.recover_timer = threading.Timer(self.test_time*2, self.timeout)
        self.recover_timer.start()

    def timeout(self):
        print("Time out occurred. Recovering")
        self.recover()

    # Called by user or timer to recover
    def recover(self): #TASK! write to a debug file
        # Invalidate the current run
        #print("Error from recover")
        self.error = True

        # Restart timer to keep recovering
        #time.sleep(120) #CHANGE!
        self.restart_timer()

        # Reconnect nodes
        for node in self.nodes:
            node.reconnect()

    # Setup various ranges based on configured profile
    #TASK! When making a new test
    def init_ranges(self):
        args = self.args
        self.loops = range(args.test_loops)
        self.test_time = args.test_time + args.test_sleep

        if args.test_profile in ('udp_rates', 'power_meas'):
            self.codings = [True, False]
            self.rates = range(args.rate_start, args.rate_stop+1, args.rate_step)
            self.test_count = len(self.rates) * args.test_loops * len(self.codings)
            self.protocol = 'udp'
            self.run_info_format = "\n# Loop: {loop:2d}/{loops:<2d} | Rate: {rate:4d} kb/s | Coding: {coding:1b} | ETA: {eta:s}"
            self.result_format = "{:10s} {throughput:6.1f} kb/s {lost:4d}/{total:<4d} {ratio:4.1f}% {ping_avg:4.1f}ms"

        if args.test_profile == "udp_ratios":
            self.codings = [True, False]
            self.rates = range(args.rate_start, args.rate_stop+1, args.rate_step)
            self.ratios = range(args.ratio_start, args.ratio_stop+1, args.ratio_step)
            self.test_count = len(self.rates) * len(self.ratios) * args.test_loops * len(self.codings)
            self.protocol = 'udp'
            self.run_info_format = "\n# Loop: {loop:2d}/{loops:<2d} | Ratio: {ratio:02d}% | Rate: {rate:4d} kb/s | Coding: {coding:1b} | ETA: {eta:s}"
            self.result_format = "{:10s} {throughput:6.1f} kb/s {lost:4d}/{total:<4d} {ratio:4.1f}%"

        if args.test_profile == 'hold_times':
            self.rates = range(args.rate_start, args.rate_stop+1, args.rate_step)
            self.hold_times = range(args.hold_start, args.hold_stop+1, args.hold_step)
            self.test_count = len(self.rates) * len(self.hold_times) * args.test_loops
            self.protocol = 'udp'
            self.run_info_format = "\n#{loop:2d}/{loops:2d} | {rate:4d} kb/s | ETA: {eta:s}"
            self.result_format = "{:10s} {throughput:6.1f} kb/s | {lost:4d}/{total:4d} ({ratio:4.1f}%)"

        if args.test_profile == 'tcp_algos':
            self.protocol = 'tcp'
            self.codings = [True, False]
            self.test_count = len(self.args.tcp_algos) * args.test_loops * len(self.codings)
            self.result_format = "{:10s} {throughput:6.1f} kb/s | {transfered:6.1f} kB"
            self.run_info_format = "\n#{loop:2d} | {tcp_algo:8s} | Coding: {coding:1b} | ETA: {eta:s}"

        if args.test_profile == 'tcp_windows':
            self.protocol = 'tcp'
            self.codings = [True, False]
            self.tcp_windows = range(args.window_start, args.window_stop+1, args.window_step)
            self.test_count = len(self.codings) * len(self.tcp_windows) * args.test_loops
            self.result_format = "{:10s} {throughput:6.1f} kb/s | {transfered:6.1f} kB"
            self.run_info_format = "\n#{loop:2d} | Window {tcp_window:5} | Coding: {coding:1b} | ETA: {eta:s}"

        if args.test_profile == 'rlnc':
            self.protocol = 'udp'
            self.codings = self.args.rlnc_codings
            self.test_count = self.args.test_loops * len(self.args.errors) * len(self.codings) * len(self.args.ack_timeout) * len(self.args.req_timeout) * len(self.args.encoders)
            self.result_format = "{:10s} {time:6.1f} s | {rate:6.1f} kb/s | {bytes:6.1f} kB | {packets:6.1f}"
            self.run_info_format = "\n#{loop:2d} | {rate:4.0f} kb/s | {coding:8s} | e: {errors} | ack: {ack_timeout:3.01f} | req: {req_timeout:3.01f} | encs: {encoders:1d} | ETA: {eta:s}"
        
        if args.test_profile == 'rasp_rank': #RASP!
            self.protocol = 'udp'
            self.codings = [True]
            self.rates = range(args.rate_start, args.rate_stop+1, args.rate_step)
            self.test_count = args.test_loops * len(self.codings)
            self.number_of_nodes = args.number_of_nodes #INDIVIDUAL_TEST!
            self.result_format = "{:10s} Received packets: {received_packets:6.1f} | Last transmitted seq num: {last_transmitted_seq_num:6.1f}"
            self.run_info_format = "\n# loop cnt:{loop:2d} | field: {field:10s}"
            self.fields = args.fields
            
        if args.test_profile == 'rasp_symbols_sweep':
            self.protocol = 'udp'
            self.symbols = range(args.symbols_start, args.symbols_stop+1, args.symbols_step)
            self.codings = [True]
            self.test_count = args.test_loops * len(self.codings)
            self.fields = args.fields #FIELDS_EXAMPLE!
            self.result_format = "{:10s} Received packets: {received_packets:6.1f} | Last transmitted seq num: {last_transmitted_seq_num:6.1f}"
            self.run_info_format = "\n# loop cnt:{loop:2d} | field: {field:10s} | symbols: {symbols:3d}"
        
        if args.test_profile == 'rasp_link_quality':
            self.protocol = 'udp'
            self.symbols = range(args.symbols_start, args.symbols_stop+1, args.symbols_step)
            self.codings = [True]
            self.test_count = args.test_loops * len(self.codings)
            self.fields = args.fields #FIELDS_EXAMPLE!
            self.number_of_nodes = args.number_of_nodes #INDIVIDUAL_TEST!
            self.result_format = "none"#"{:10s} Received packets: {received_packets:6.1f} | Last transmitted seq num: {last_transmitted_seq_num:6.1f}"
            self.run_info_format ="\n# loop cnt:{loop:2d} | field: {field:10s} | symbols: {symbols:3d}"
            #RASP! NEW_TEST! TEST_SPECIFIC_SETUP!
        
    # Configure the next run_info to be sent to each node
    def set_run_info(self,  **kwarg):
        #print("# Setting run info")  #DEBUG!
        self.update_run_no(kwarg.get('loop'))
        self.run_info['profile'] = self.args.test_profile
        self.run_info['test_time'] = self.args.test_time
        self.run_info['sample_interval'] = self.args.sample_interval
        self.run_info['protocol'] = self.protocol
        self.run_info['tcp_algo'] = kwarg.get('tcp_algo')
        self.run_info['loop'] = kwarg.get('loop')
        self.run_info['rate'] = kwarg.get('rate')
        self.run_info['hold'] = kwarg.get('hold')
        self.run_info['purge'] = kwarg.get('purge')
        self.run_info['coding'] = kwarg.get('coding')
        self.run_info['tcp_window'] = kwarg.get('tcp_window')
        self.run_info['promisc'] = kwarg.get('coding')
        self.run_info['ratio'] = kwarg.get('ratio')
        self.run_info['rts'] = self.args.rts_threshold
        self.run_info['gen_size'] = self.args.gen_size
        self.run_info['packet_size'] = self.args.packet_size
        self.run_info['iperf_len'] = self.args.iperf_len
        self.run_info['fixed_overshoot'] = self.args.fixed_overshoot.get(kwarg.get('coding'))
        self.run_info['encoders'] = kwarg.get('encoders')
        self.run_info['encoder_timeout'] = self.args.encoder_timeout
        self.run_info['decoder_timeout'] = self.args.decoder_timeout
        self.run_info['recoder_timeout'] = self.args.recoder_timeout
        self.run_info['helper_timeout'] = self.args.helper_timeout
        self.run_info['helper_overshoot'] = self.args.helper_overshoot
        self.run_info['fox_verbose'] = self.args.fox_verbose
        self.run_info['helper_threshold'] = self.args.helper_threshold
        self.run_info['systematic'] = self.args.systematic
        self.run_info['errors'] = kwarg.get('errors')
        self.run_info['ack_timeout'] = kwarg.get('ack')
        self.run_info['req_timeout'] = kwarg.get('req')
        self.run_info['test_num'] = self.test_num
        self.run_info['field'] = kwarg.get('field') #PASP! ADD syntax when comming from riddler_defaults.py
        self.run_info['max_tx'] = self.args.max_tx #RASP! ADD_ARG! syntax when comming from parser
        self.run_info['number_of_nodes'] = self.args.number_of_nodes
        self.run_info['filename'] = self.args.filename
        self.run_info['symbols'] = kwarg.get('symbols')
        self.run_info['id'] = kwarg.get('id')
        self.run_info['linkquality'] = kwarg.get('linkquality')
        #INDIVIDUAL_NODE! ADD the individual id
        
        # Update the data storage with the new run info
        #print self.run_info
        self.data.add_run_info(self.run_info)#INDIVIDUAL_NODE! uncomment

    def update_run_info_individual_settings(self, j):
        for i in range(len(self.individual_info[0])):
            self.run_info[self.individual_info[0][i]] = self.individual_info[i+1][j]
    
    # Reset counter if new loop is entered, increment otherwise
    def update_run_no(self, loop):
        if not self.run_info or loop != self.run_info['loop']:
            # We are in a new loop
            self.run_info['run_no'] = 0
        else:
            # Same loop as before
            self.run_info['run_no'] += 1

    # Tell each node to prepare a new run and wait for them to become ready
    def prepare_run(self):
        #print("# Preparing run")  #DEBUG!
        # We start from a clean sheet
        self.error = False

        # Start timer to recover in case of failure
        self.restart_timer()
        j = 0
        for node in self.nodes:#INDIVIDUAL_NODE!
            #INDIVIDUAL_NODE! Insert a function which update run_info with individual data
            #Two methods look at test or node type
            if self.individual_info:
                self.update_run_info_individual_settings(j)
            node.prepare_run(self.run_info)
            j = j + 1
        
        for node in self.nodes:
            node.wait()
        
    # Perform a run on each node
    def exec_node(self):
        print("# STARTING NODES")  #DEBUG!
        # Start it
        for node in self.nodes:
            time.sleep(0.01)
            node.start_run()
        #print("# STARTING NODES ARE STARTED") #DEBUG!
        # Wait for it to finish
        print("# WAIT FOR RESULT")
        for node in self.nodes:
            # Check if an error occurred in the run
            if node.wait():
                print("controller wait error from {}".format(node.name))
                self.error = True

        if self.error and not self.end.is_set():
            for node in self.nodes:
                node.reconnect()
        print("# DONE EXECUTING NOTES")
    # Tell the nodes to clean up and wait for them to report back
    def finish_run(self):
        print("# FINNISH RUN")  #DEBUG!
        for node in self.nodes:
            node.finish_run()

        for node in self.nodes:
            node.wait()

        self.recover_timer.cancel()

    
    def save_results(self):
        print("# SAVE RESULTS")  #DEBUG!
        for node in self.nodes:
            #print "node:", node #DEBUG!
            result = node.get_result()

            # Some nodes don't measure results
            if not result:
                continue
            self.data.add_result(node.name, result, self.run_info)
            self.print_result(node, result)
            #print "save_result riddler_controller result:",result 
            

    # Save sample measurements received during the test
    def save_samples(self):
        for node in self.nodes:
            samples = node.get_samples()
            if not samples:
                return False
            self.data.add_samples(node.name, samples)
        return True

    def format_time(self, total_time):
        if total_time > 60*60:
            time_str = "{}h {:2}m".format(int(total_time/60/60), int((total_time/60)%60))
        else:
            time_str = "{}m {:2}s".format(int(total_time/60), int(total_time%60))
        return time_str

    # Report the result to the user
    def print_result(self, node, result):
        print(self.result_format.format(node.name.title(), **result))

    # Print info on the current test run
    def print_run_info(self, run_info):
        if self.end.is_set():
            return

        eta = self.test_count * self.test_time
        if eta > 60*60:
            # Print ETA with hours
            eta = "{:d}h {:02d}m".format(eta/60/60, (eta/60)%60)
        else:
            # Print ETA with minutes
            eta = "{:d}m {:02d}s".format(eta/60, eta%60)

        print(self.run_info_format.format(eta=eta, loops=self.args.test_loops-1, **run_info))
