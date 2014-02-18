import riddler_node as node


#alice = node.node("source", "localhost")
#bob = node.node("destination", "localhost", 8898)
alice = node.node("source", "rasp12.lab.es.aau.dk")

bob = node.node("destination", "rasp15.lab.es.aau.dk")
#catja = node.node("destination", "rasp02.lab.es.aau.dk")
#d = node.node("destination", "rasp03.lab.es.aau.dk")
#e = node.node("destination", "rasp05.lab.es.aau.dk")
#f = node.node("destination", "rasp10.lab.es.aau.dk")
#dan = node.node("destination", "rasp04.lab.es.aau.dk")


#Add destinations to sourcerasp09
alice.add_dest(bob) #Alice client bob server
#alice.add_dest(catja)
#alice.add_dest(d) #Alice client bob server
#alice.add_dest(e)
#alice.add_dest(f) #Alice client bob server
#alice.add_dest(dan)

#Add source to destinations
bob.add_source(alice)
#catja.add_source(alice)
#d.add_source(alice)
#e.add_source(alice)
#f.add_source(alice)
#dan.add_source(alice)

#bob.add_dest(alice)
#bob.set_enable_ratio(True)


"""
#RASP! LOCAL_TEST!
alice = node.node("source", "localhost")
bob = node.node("destination_1", "localhost", 8898)

alice.add_dest(bob)
#alice.add_dest(dan)

#Add source to destinations
#bob.add_source(alice)
bob.add_source(alice)
"""

