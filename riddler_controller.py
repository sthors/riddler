import time
import threading
import riddler_interface as interface
import riddler_data as data

class controller(threading.Thread):
    def __init__(self, args, nodes):
        super(controller, self).__init__(None)
        self.name = "controller"
        self.args = args
        self.nodes = nodes

        # Load data object
        self.data = data.data(nodes, args.test_profile)

        self.error = False
        self.recover_timer = None
        self.end = threading.Event()
        self.pause = threading.Event()
        self.daemon = True

    # Stop the controller
    def stop(self):
        # Tell thread to stop
        self.end.set()

    # Toggle the pause event to pause tests
    def toggle_pause(self):
        if self.pause.is_set():
            # Pause: on
            self.pause.clear()
        else:
            # Pause: off
            self.pause.set()

    def run(self):
        self.pause.set()

        try:
            self.control()
        except KeyboardInterrupt:
            return

    def control(self):
        self.init_ranges()
        profile = self.args.test_profile

        # Select control function based on configured profile
        if profile in ("udp_rates","power_meas"):
            self.test_rates()

        elif profile == "tcp_algos":
            self.test_tcp_algos()

        elif profile == "hold_times":
            self.test_hold_times()

        else:
            print("Profile '{0}' not supported.".format(profile))
            return

        # Yeah, the test actually completed by itself
        if not self.end.is_set():
            print("Test completed")

    def save_data(self, path=None):
        if not path:
            path = self.args.data_file

        # Dump data to pickle file
        data.dump_data(self.data, path)

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

    # Control function to swipe TCP congestion avoidance algorithms
    def test_tcp_algos(self):
        hold = self.args.hold_time
        purge = self.args.purge_time

        for loop in self.loops:
            for algo in self.args.tcp_algos:
                for coding in self.codings:
                    self.set_run_info(loop=loop, hold=hold, purge=purge, coding=coding, tcp_algo=algo)
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

    # Control the state of each node and execute a single test run
    def execute_run(self):
        while not self.end.is_set():
            # Make time stamp for use in ETA
            start = time.time()

            # Let the network settle before next test
            time.sleep(self.args.test_sleep)

            # Check if we should pause and rerun
            self.wait_pause()

            self.print_run_info(self.run_info)
            self.prepare_run()

            # Wait for run to finish and check the result
            self.exec_node()

            # Let the nodes clean up and save data
            self.finish_run()

            # Check if we should pause and rerun
            self.wait_pause()

            # Decide on the next action
            if self.end.is_set():
                # Quit
                return

            elif not self.error:
                # Successful test
                self.save_results()
                self.save_samples()

                # Update test count
                self.test_count -= 1
                self.test_time = int(time.time() - start)
                break

            else:
                # Test failed, run it again
                print("Redoing test")

    # Check if pause is requested and pause if so
    def wait_pause(self):
        # Check the user setting
        if self.pause.is_set():
            # Nope, we don't pause
            return False

        # Invalidate current run
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
        self.recover_timer = threading.Timer(self.args.test_time*2, self.timeout)
        self.recover_timer.start()

    def timeout(self):
        print("Time out occurred. Recovering")
        self.recover()

    # Called by user or timer to recover
    def recover(self):
        # Invalidate the current run
        self.error = True

        # Restart timer to keep recovering
        self.restart_timer()

        # Reconnect nodes
        for node in self.nodes:
            node.reconnect()

    # Setup various ranges based on configured profile
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
            self.result_format = "{:10s} {throughput:6d} kb/s {lost:4d}/{total:<4d} {ratio:4.1f}%"

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
            self.run_info_format = "\n#{loop:2d} | {tcp_algo:10s} | Coding: {coding:1b} | ETA: {eta:s}"

    # Configure the next run_info to be sent to each node
    def set_run_info(self, loop=None, rate=None, hold=None, purge=None, coding=None, tcp_algo=None):
        self.run_info = {}
        self.run_info['test_time'] = self.args.test_time
        self.run_info['sample_interval'] = self.args.sample_interval
        self.run_info['protocol'] = self.protocol
        self.run_info['tcp_algo'] = tcp_algo
        self.run_info['loop'] = loop
        self.run_info['rate'] = rate
        self.run_info['hold'] = hold
        self.run_info['purge'] = purge
        self.run_info['coding'] = coding

        # Update the data storage with the new run info
        self.data.new_run(self.run_info)

    # Tell each node to prepare a new run and wait for them to become ready
    def prepare_run(self):
        # We start from a clean sheet
        self.error = False

        # Start timer to recover in case of failure
        self.restart_timer()

        for node in self.nodes:
            node.prepare_run(self.run_info)

        for node in self.nodes:
            node.wait()

    # Perform a run on each node
    def exec_node(self):
        ret = True

        # Start it
        for node in self.nodes:
            node.start_run()

        # Wait for it to finish
        for node in self.nodes:
            # Check if an error occurred in the run
            if node.wait():
                self.error = True

    # Tell the nodes to clean up and wait for them to report back
    def finish_run(self):
        for node in self.nodes:
            node.finish_run()

        for node in self.nodes:
            node.wait()

        self.recover_timer.cancel()

    # Store measured data
    def save_results(self):
        for node in self.nodes:
            result = node.get_result()
            # Some nodes don't measure results
            if not result:
                continue
            self.data.save_result(node.name, result)
            self.print_result(node, result)

    # Save sample measurements received during the test
    def save_samples(self):
        for node in self.nodes:
            samples = node.get_samples()
            self.data.append_samples(node.name, samples)

    # Report the result to the user
    def print_result(self, node, result):
        print(self.result_format.format(node.name.title(), **result))

    # Print info on the current test run
    def print_run_info(self, run_info):
        eta = self.test_count * self.test_time
        if eta > 60:
            # Print ETA with hours
            eta = "{:d}h {:02d}m".format(eta/60/60, (eta/60)%60)
        else:
            # Print ETA with minutes
            eta = "{:d}m {:02d}s".format(eta/60, eta%60)

        print(self.run_info_format.format(eta=eta, loops=self.args.test_loops-1, **run_info))
