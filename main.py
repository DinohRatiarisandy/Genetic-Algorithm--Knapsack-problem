import sys, os
from random import choices, randint, randrange, random
from typing import Tuple, List, Optional, Callable
from collections import namedtuple
from functools import partial
from PyQt6 import QtWidgets, QtGui
from PyQt6.QtWidgets import QTableWidgetItem
from gui_genetic_algorithm import Ui_AlgoGenetique


# ---------------------------------------------------------------------------
Genome = List[int]
Population = List[Genome]
FitnessFunc = Callable[[Genome], int]
PopulateFunc = Callable[[], Population]
SelectionFunc = Callable[[Population, FitnessFunc], Tuple[Genome, Genome]]
CrossoverFunc = Callable[[Genome, Genome], Tuple[Genome, Genome]]
MutationFunc = Callable[[Genome], Genome]

Thing = namedtuple('Thing', ['name', 'value', 'weight'])

# things1 = [
# 	Thing('Boussole', 12, 5),
# 	Thing('Eau', 5, 3),
# 	Thing('Chapeau', 10, 7),
# 	Thing('Lampe de poche', 7, 2),
# ]

def generate_genome(lenght: int) -> Genome:
	return choices([0, 1], k=lenght)

def generate_population(size: int, genome_lenght: int) -> Population:
	return [generate_genome(genome_lenght) for _ in range(size)]

def fitness(genome: Genome, things: List[Thing], weight_limit: int) -> int:
	if len(genome)!=len(things):
		raise ValueError("Genome and things must be of the same lenght")

	weight = 0
	value = 0

	for i, thing in enumerate(things):
		if genome[i]==1:
			weight += thing.weight
			value += thing.value

			if weight>weight_limit:
				return 0
	return value

def selection_pair(population: Population, fitness_func: FitnessFunc) -> Population:
	return choices(
		population=population,
		weights=[fitness_func(genome) for genome in population],
		k=2
	)

def single_point_crossover(a: Genome, b: Genome) -> Tuple[Genome, Genome]:
	if len(a)!=len(b):
		raise ValueError("Genome a and b must be of same lenght")

	p = randint(1, len(a)-1)

	if len(a)<2:
		return a, b

	return a[:p]+b[p:], b[:p]+a[p:]

def mutation(genome: Genome, num: int=1, probability: float=0.65) -> Genome:
	for _ in range(num):
		idx = randrange(len(genome))
		genome[idx] = genome[idx] if random()>probability else abs(genome[idx]-1)

	return genome

def run_evolution(
	populate_func: PopulateFunc,
	fitness_func: FitnessFunc,
	fitness_limit: int,
	selection_func: SelectionFunc=selection_pair,
	crossover_func: CrossoverFunc=single_point_crossover,
	mutation_func: MutationFunc=mutation,
	generation_limit: int=100
) -> Tuple[Population, int]:
	population = populate_func()
	for i in range(generation_limit):
		population = sorted(
			population,
			key=lambda genome: fitness_func(genome),
			reverse=True
		)

		if fitness_func(population[0])>fitness_limit:
			break
		next_generation = population[:2]

		for j in range(len(population)//2 - 1):
			parents = selection_func(population, fitness_func)
			offspring_a, offspring_b = crossover_func(parents[0], parents[1])
			offspring_a = mutation_func(offspring_a)
			offspring_b = mutation_func(offspring_b)
			next_generation += [offspring_a, offspring_b]

		population = next_generation
		population = sorted(population, key=lambda genome: fitness_func(genome), reverse=True)

	return population, i

def genome_to_things(genome: Genome, things: List[Thing]) -> List[Thing]:
	result = []
	for i, thing in enumerate(things):
		if genome[i]==1:
			result += [thing.name]
	return result

def creat_app():
	app = QtWidgets.QApplication(sys.argv)
	win = Window()
	win.show()
	sys.exit(app.exec())

# ---------------------------------------------------------------------------
base_dir = os.path.dirname(__file__)

class Window(QtWidgets.QMainWindow):
	def __init__(self):
		super(Window, self).__init__()
		self.things = []
		self.ui = Ui_AlgoGenetique()
		self.setWindowIcon(QtGui.QIcon(os.path.join(base_dir, "logo.ico")))
		self.ui.setupUi(self)

		self.ui.addButton.clicked.connect(self.add_item)
		self.ui.solveButton.clicked.connect(self.solve)
		self.ui.clearAll.clicked.connect(self.clear_all)

	def clear_all(self):
		self.things = []
		self.ui.listSolution.clear()

		# remove items in the table widget
		row_count = self.ui.itemsBag.rowCount()
		while row_count>0:
			self.ui.itemsBag.removeRow(row_count-1)
			row_count -= 1

		# set all value to default
		self.ui.lineName.clear()
		self.ui.value.setValue(25.0)
		self.ui.weight.setValue(5)
		self.ui.probability.setValue(65.0)
		self.ui.desiredAmount.setValue(1000.0)
		self.ui.startingPopulation.setValue(10)
		self.ui.generationMax.setValue(100)

	def add_item(self):
		name = self.ui.lineName.text()
		value = self.ui.value.value()
		weight = self.ui.weight.value()

		if name and value and weight is not None:
			row_count = self.ui.itemsBag.rowCount()
			self.ui.itemsBag.insertRow(row_count)
			self.ui.itemsBag.setItem(row_count, 0, QTableWidgetItem(str(name)))
			self.ui.itemsBag.setItem(row_count, 1, QTableWidgetItem(str(value)))
			self.ui.itemsBag.setItem(row_count, 2, QTableWidgetItem(str(weight)))
			self.things.append(Thing(name, float(value), float(weight)))
			self.ui.lineName.clear()

	def solve(self):
		weight_max = self.ui.weightMax.value()
		probability = self.ui.probability.value() / 100
		desired_amount = self.ui.desiredAmount.value()
		starting_population = self.ui.startingPopulation.value()
		generation_max = self.ui.generationMax.value()

		if self.things != [] and weight_max and probability and desired_amount and starting_population and generation_max is not None:

			population, generations = run_evolution(
				populate_func=partial(
					generate_population, size=starting_population, genome_lenght=len(self.things)
				),
				fitness_func=partial(fitness, things=self.things, weight_limit=weight_max),
				fitness_limit=desired_amount,
				generation_limit=generation_max
			)

			def print_solution(genome: Genome, things: List[Thing]) -> List[Thing]:
				self.ui.listSolution.clear()
				for i, thing in enumerate(things):
					if genome[i]==1:
						self.ui.listSolution.addItem(thing.name)

			print_solution(population[0], self.things)

# ---------------------------------------------------------------------------
if __name__ == "__main__":	
	creat_app()

