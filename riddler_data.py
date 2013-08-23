import time
import copy
import cPickle as pickle
import pandas as pd
import os

"""
Data structure:

    data = {
        'node0': {
            '0': [ run_data, run_data, ... ],
            '1': [ run_data, run_data, ... ],
            ...
        },
        'node1': {
            '0': [ run_data, run_data, ... ],
            '1': [ run_data, run_data, ... ],
            ...
        },
        ...
    }

Node dictionaries contain a list for each run_no. These lists contain
run_data objects for each loop in the test. When retrieving data,
each run_data contains a run_info dictionary, which can be used to
determine relevant parameters.
"""

class run_data:
    def __init__(self, run_info):
        self.run_info = run_info
        self.result = []
        self.samples = []

class data:
    def __init__(self, args):
        self.args = args
        self.nodes = []
        self.sources = []
        self.relays = []
        self.macs = {}
        self.rd = {}

    def add_nodes(self, nodes):
        for node in nodes:
            name = node.name
            self.rd[name] = []
            self.macs[name] = node.mesh_mac
            if node.dests:
                self.sources.append(name)
            else:
                self.relays.append(name)

    def add_run_info(self, run_info):
        run_info = copy.deepcopy(run_info)
        run_no = run_info['run_no']
        loop = run_info['loop']

        for node in self.rd:
            if loop == 0:
                self.rd[node].append([])

            rd = run_data(run_info)
            self.rd[node][run_no].append(rd)
        self.run_no = run_no

    def add_samples(self, node, samples):
        # Add samples to latest run_data
        d = self.rd[node][self.run_no][-1]
        d.samples = samples

    def add_result(self, node, result, **kwargs):
        # Add result to latest run_data
        d = self.rd[node][self.run_no][-1]
        d.result = result
        print "riddler_data add_result:", d.result

    def get_run_data_node(self, node, conditions):
        d = self.rd[node]
        test = lambda rd, k, v: rd[0].run_info[k] == v

        for key,val in conditions.items():
            d = filter(lambda rd: test(rd, key, val), d)
        return d
        
    def save_csv(self, csv_path):
        #csv_path = csv_path + ".csv"
        for i in range(1000):
            csv_full_path = csv_path + "_" + str(i+1) +".csv"
            if not os.path.exists(csv_full_path):
                df = pd.DataFrame(self.results)
                df.to_csv(csv_full_path)
                return
            else:
                pass
        print("Error: cannot save csv file. perhaps to many tests today with the same name!")


def dump_data(data, filename):
    f = open(filename, 'w')
    pickle.dump(data, f, pickle.HIGHEST_PROTOCOL)
    f.close()
    
    
class data_pandas:
    def __init__(self, args):
        self.args = args
        self.nodes = []
        self.sources = []
        self.relays = []
        self.macs = {}
        self.rd = {}
        self.results = []
        
    def add_nodes(self, nodes):
        pass

    def add_run_info(self, run_info):
        pass

    def add_samples(self, node, samples):
        pass

    def add_result(self, node, result, run_info, **kwargs):
        kwargs.update(run_info)
        kwargs.update(result)
        kwargs.update({"node":node})
        self.results.append(kwargs)
        # Add result to latest run_data
        #d = self.rd[node][self.run_no][-1]
        #d.result = result
        #print "riddler_data add_result:", self.results
        
    def save_csv(self):
        #csv_path = csv_path + ".csv"
        for i in range(1000):
            csv_full_path = self.args.filename + "_" + str(i+1) +".csv"
            if not os.path.exists(csv_full_path):
                df = pd.DataFrame(self.results)
                df.to_csv(csv_full_path)
                self.csv_full_path = csv_full_path
                print self.csv_full_path
                return
            else:
                pass
        print("Error: cannot save csv file. perhaps to many tests today with the same name!")
            
    def load_csv(self):
        self.df = pd.read_csv(self.csv_full_path)
        return self.df
        """
        csv_path = csv_path + ".csv"
        df = pd.DataFrame(self.results)
        df.to_csv(csv_path)
        """
    def plot_rank(self):
        pass
