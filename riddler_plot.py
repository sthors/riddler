import matplotlib.pyplot as plt
#from collections import ChainMap
import numpy as np
import pandas as pd

class plot:
    def __init__(self, data):
        self.df = data

    def plot_rank(self): #ADD_PLOT_FUNTION!
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
                    ranks.mean().plot(kind="bar",label=node)
                    #break
                #plt.legend("coding","symbols","field")
                #break
            plt.show()
            
    def plot_last_received_seq_num(self): #TASK! not finished
            if not self.df:
                return
            #print self.df
            
            groups = self.df.groupby(['received_packets', 'field'])
            for (symbols,field),df in groups:
                plt.figure()
                plt.title(str((symbols,field)))
                for node,d in df.groupby('node'):
                    ranks = d['ranks'].apply(lambda x: pd.Series(eval(x)))
                    #print "ranks:", ranks
                    ranks.mean().plot(kind="bar",label=node)
                    #break
                #plt.legend("coding","symbols","field")
                #break
            plt.show()
