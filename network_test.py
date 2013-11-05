import riddler_node as node

"""
alice = node.node("alice", "panda0.personal.es.aau.dk")
relay = node.node("relay", "panda1.personal.es.aau.dk")
bob = node.node("bob", "panda2.personal.es.aau.dk")
mhu = node.node("mhu", "localhost")
alice = node.node("alice", "panda5.personal.es.aau.dk")
bob = node.node("bob", "panda6.personal.es.aau.dk")
"""

#alice = node.node("source", "localhost")
#bob = node.node("destination", "localhost", 8898)
alice = node.node("source", "rasp00.lab.es.aau.dk")
bob = node.node("destination", "rasp10.lab.es.aau.dk")
#catja = node.node("destination", "rasp09.lab.es.aau.dk")
#dan = node.node("destination", "rasp04.lab.es.aau.dk")


#Add destinations to sourcerasp09
alice.add_dest(bob) #Alice client bob server
#alice.add_dest(catja)
#alice.add_dest(dan)

#Add source to destinations
bob.add_source(alice)
#catja.add_source(alice)
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
"""
alice = node.node("alice", "panda5.personal.es.aau.dk")
relay = node.node("relay", "panda6.personal.es.aau.dk")
bob = node.node("bob", "panda7.personal.es.aau.dk")
"""
