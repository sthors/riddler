import matplotlib.pyplot as plt
#from collections import ChainMap
import numpy as np
import pandas as pd

class plot:
    def __init__(self, plot_types, data):
        self.plot_types = plot_types
        self.df = data

    def plot_rank(self):
            if not self.df:
                return
            #print self.df
            
            groups = self.df.groupby(['symbols', 'field'])
            for (symbols,field),df in groups:
                plt.figure()
                plt.title(str((symbols,field)))
                for node,d in df.groupby('node'):
                    ranks = d['ranks'].apply(lambda x: pd.Series(eval(x)))
                    #print "ranks:", ranks
                    ranks.mean().plot(label=node)
                    #break
                #plt.legend("coding","symbols","field")
                #break
            plt.show()
