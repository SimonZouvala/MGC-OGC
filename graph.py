import sys
import matplotlib.pyplot as plt
import math
import numpy as np

from matplotlib.ticker import AutoMinorLocator, LinearLocator
from collections import defaultdict


class Graph:
    def __init__(self, data):
        self.first_data, self.second_data = data
        self.data1, self.data2 = load_files(self.first_data), load_files(self.second_data)
        self.ready1, self.ready2 = compare_data(self.data1, self.data2)
        graph(self.ready1, self.ready2, data)


def load_files(file):
    try:
        molecule = []
        with open(file, "r") as f1:
            while True:
                element_charge, line = [], f1.readline()
                if "" == line[0:1]:
                    data = sorted(molecule)
                    break
                name = line[:].strip()
                line = f1.readline()
                count = int(line[:].strip())
                for i in range(count):
                    line = f1.readline()
                    element = line[6:11].strip()
                    charge = float(line[11:].strip())
                    element_charge.append((element, charge))
                molecule.append((name, element_charge))
    except IOError:
        print("Wrong file for graph! Try another file than {}".format(file))
        sys.exit(1)
    return data


def compare_data(data1, data2):
    first_data, second_data = [], []
    for name1, elements1 in data1:
        for name2, elements2 in data2:
            if name1 == name2:
                first_data.append(elements1)
                second_data.append(elements2)
                continue
    ready1 = prepare_data(first_data)
    ready2 = prepare_data(second_data)
    return ready1, ready2


def graph(ready1, ready2, filenames):
    fig, ax = plt.subplots(figsize=(12, 12))
    minimum, maximum = draw_data(ready1, ready2)
    ax.legend(loc=2)
    ax.yaxis.set_minor_locator(AutoMinorLocator())
    ax.xaxis.set_minor_locator(AutoMinorLocator())
    ax.yaxis.set_major_locator(LinearLocator())
    ax.xaxis.set_major_locator(LinearLocator())
    plt.tick_params(which='major', length=5, width=2)
    plt.tick_params(which='minor', length=5)
    plt.xlim(minimum - 0.05, maximum + 0.05)
    #plt.ylim(minimum - 0.05, maximum + 0.05)
    ax.set_title("Correlation graph")
    ax.set_ylabel("Charge from {}".format(filenames[1]))
    ax.set_xlabel("Charge from {}".format(filenames[0]))
    plt.show()


def draw_data(element_data1, element_data2):
    mistakes, minimum, maximum, yminimum, ymaximum = [], 99999, -99999, 99999, -999999
    pcc_graph = get_pcc_for_all_graph(element_data1, element_data2)
    for element1, element2 in zip(element_data1, element_data2):
        yminimum = min(min(element_data2[element2]), yminimum)
        ymaximum = max(max(element_data2[element2]), ymaximum)
        minimum = min(minimum, min(element_data1[element1]), min(element_data2[element2]))
        maximum = max(maximum, max(element_data1[element1]), max(element_data2[element2]))
        plt.scatter(element_data1[element1], element_data2[element2], marker="o", label=element1, alpha=0.9)
        mistakes.append(get_mistake(element_data1[element1], element_data2[element2], element1))
    plt.plot([minimum, maximum], [yminimum, ymaximum * pcc_graph])
    print_mistake(mistakes, pcc_graph)
    return minimum, maximum


def print_mistake(mistakes, pcc_graph):
    print("Element          MAD     MAXIMUM     RMSD        PCC")
    for element, mad, maximum, rmsd, pcc in mistakes:
        print("{:<10} {: >9.3} {: >11.3} {: >8.3} {: >10.3}".format(element, mad, maximum, rmsd, pcc))
    print("r = {}". format(pcc_graph))


def get_mistake(charges1, charges2, element):
    maximum, data_for_rmsd, sum_x, sum_y = abs(charges1[0] - charges2[0]), 0, 0, 0
    charges = charges1 + charges2
    value = 0
    data_x, data_y = [], []
    for x, y in zip(charges1, charges2):
        maximum = max(maximum, abs(x - y))
        sum_x += x
        sum_y += y
    mean = (sum_x+sum_y)/(len(charges1)+len(charges2))
    for charge in charges:
        value += abs(charge - mean)
    mad = value/len(charges)
    for x, y in zip(charges1, charges2):
        data_for_rmsd += (x - y)**2
        data_x.append(x)
        data_y.append(y)
    rmsd = math.sqrt((data_for_rmsd/len(charges1)))
    try:
        pcc = np.corrcoef(data_x, data_y)[1, 0]
    except ArithmeticError:
        pcc = 0.0
        pass
    return [element, mad, maximum, rmsd, pcc]


def prepare_data(crude_data):
    element_data, elements = defaultdict(list), []
    for molecule in crude_data:
        elements = [element for element, _ in molecule]
        for e in set(elements):
            element_data[e].extend(list([charge for element, charge in molecule if element == e]))
    return element_data


def get_pcc_for_all_graph(charges1, charges2):
    data_x, data_y = [], []
    for i, j in zip(charges1, charges2):
        for x, y in zip(charges1[i], charges2[j]):
            data_x.append(x)
            data_y.append(y)
    pearr = np.corrcoef(data_x, data_y)[1, 0]
    return pearr
