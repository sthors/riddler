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
alice = node.node("source", "rasp01.lab.es.aau.dk")
bob = node.node("destination", "rasp02.lab.es.aau.dk")
catja = node.node("destination", "rasp00.lab.es.aau.dk")
"""
alice = node.node("alice", "panda5.personal.es.aau.dk")
relay = node.node("relay", "panda6.personal.es.aau.dk")
bob = node.node("bob", "panda7.personal.es.aau.dk")
"""
#Add destinations to source
alice.add_dest(bob) #Alice client bob server
alice.add_dest(catja)

#Add source to destinations
bob.add_source(alice)
catja.add_source(alice)

#bob.add_dest(alice)
#bob.set_enable_ratio(True)
