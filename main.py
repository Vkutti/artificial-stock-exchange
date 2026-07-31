from exchange.exchange import Exchange
from simulation.simulation import Simulation

exchange = Exchange()

simulation = Simulation(exchange)

simulation.run()