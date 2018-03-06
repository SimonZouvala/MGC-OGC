import sys
import numpy as np
import re

from collections import Counter


class Atom:
    def __init__(self, number, element_symbol, bond, coordinate=0):
        self.element_symbol = element_symbol
        self.coordinate = coordinate
        self.bond = bond
        self.number = number

    def __str__(self):
        return str("{} {} {} {}".format(self.number, self.element_symbol, self.bond, self.coordinate))


class Molecule:

    def __init__(self, name, count_atoms, atoms, elements_count, count_bond_matrix, bond_matrix):
        self.name = name
        self.count_atoms = count_atoms
        self.atoms = atoms
        self.elements_count = elements_count
        self.count_bond_matrix = count_bond_matrix
        self.bond_matrix = bond_matrix

    def __str__(self):
        return str("Molecule name: {}\n{}".format(self.name, self.atoms))


class MoleculesSet:
    def load_from_sdf(self, filename, eem, mgchm, ogchm, yes_type=True):
        molecules, find_elements = [], []
        try:
            with open(filename, "r") as fh:
                while True:
                    max_bond, atoms, elements, coordinate, line, elements_count = Counter(), [], [], [], fh.readline(),\
                                                                                  Counter()
                    shift, element_true = Counter(), {}
                    if "" == line[0:1]:
                        self.molecules = molecules
                        if mgchm:
                            self.periodic_table = get_electronegativity_from_periodic_table(set(find_elements))
                        if ogchm:
                            self.tb_el = table_electronegativity
                            self.tb_hard = table_hardness
                        return print("Load molecules from {}".format(filename))
                    name = (line[:].strip())
                    for i in range(2):
                        fh.readline()
                    line = fh.readline()
                    count_atoms, count_bonds = int(line[0:3]), int(line[3:6])
                    for i in range(1, count_atoms + 1):
                        line = fh.readline()
                        elements.append(line[31:33].strip())
                        if eem:
                            coordinate.append((float(line[2:10]), float(line[12:20]), float(line[22:30])))
                        if mgchm or ogchm:
                            find_elements.append(line[31:33].strip())
                            element_true[i] = True
                    if ogchm:
                        size_matrix, orbital_electrons = get_orbital_electrons(elements)
                        count_bond_matrix = np.zeros((size_matrix, size_matrix))
                        bond_matrix = np.zeros((size_matrix, size_matrix))
                        table_electronegativity = np.zeros((size_matrix, 1))
                        table_hardness = np.zeros((size_matrix, 1))
                    if mgchm:
                        count_bond_matrix = np.zeros((count_atoms, count_atoms))
                        bond_matrix = np.zeros((count_atoms, count_atoms))
                    for i in range(count_bonds):
                        line = fh.readline()
                        first_atom, second_atom, bond = int(line[1:3]), int(line[3:6]), int(line[8:9])
                        max_bond[first_atom] = max(max_bond[first_atom], bond)
                        max_bond[second_atom] = max(max_bond[second_atom], bond)
                        if mgchm:
                            index1, index2 = first_atom - 1, second_atom - 1
                            bond_matrix[index1, index2] = bond_matrix[index2, index1] = bond
                            count_bond_matrix[index1, index1] += bond
                            count_bond_matrix[index2, index2] += bond
                        if ogchm:
                            orbital_electrons[0] = []
                            position1 = position2 = 0
                            for valence in range(0, first_atom):
                                position1 += len(orbital_electrons[valence])
                            for valence in range(0, second_atom):
                                position2 += len(orbital_electrons[valence])
                            number_element = first_atom
                            position = position1
                            for i in range(2):
                                if max_bond[number_element] == bond and element_true[number_element]:
                                    state_text = []
                                    valence_electrons = len(orbital_electrons[number_element])
                                    electron_states = ["s", "di", "tr", "te"]
                                    filled_type_state = 1
                                    non_binding_pair = 0
                                    if bond == 1:
                                        if valence_electrons in [1, 2 ,3 , 4]:
                                            for x in range(valence_electrons):
                                                state_text.append(electron_states[valence_electrons - 1])
                                                index_state = valence_electrons - 1
                                                non_binding_pair = 4

                                        else:
                                            for y in range(valence_electrons//4):
                                                state_text.append(electron_states[valence_electrons - 1] + "2")
                                                non_binding_pair += 1
                                                index_state = 3
                                    else:
                                        for x in range(bond - 1):
                                            state_text.append("pi")
                                            valence_electrons -= 1
                                            filled_type_state += 1
                                        if (filled_type_state > 2) and ((valence_electrons/2) >= 1.5):
                                            for y in range(valence_electrons//2):
                                                state_text.append(electron_states[-filled_type_state] + "2")
                                                non_binding_pair += 1
                                        index_state = -filled_type_state
                                    for y in range(4 - filled_type_state + 1 - non_binding_pair):
                                        state_text.insert(0, electron_states[index_state])
                                    electronegativity, hardness = get_electronnegativity_and_hardness(
                                        state_text, find_elements[number_element - 1])
                                    print(state_text)
                                    for i, state in enumerate(state_text):
                                        table_electronegativity[position + i][0] = electronegativity[
                                            find_elements[number_element - 1], state]
                                        table_hardness[position + i][0] = hardness[find_elements[number_element - 1],
                                                                                   state]
                                        if "2" in state:
                                            position += 1
                                            table_electronegativity[position + i][0] = electronegativity[
                                                find_elements[number_element - 1], state]
                                            table_hardness[position + i][0] = hardness[find_elements[
                                                                                           number_element - 1], state]
                                position = position2
                                element_true[number_element] = False
                                number_element = second_atom
                            for x in range(bond):
                                bond_matrix[position1 + shift[first_atom]][position2 + shift[second_atom]] = \
                                    bond_matrix[position2 + shift[second_atom]][position1 + shift[first_atom]] = 1
                                shift[first_atom] += 1
                                shift[second_atom] += 1
                    if ogchm:
                        position = 0
                        for valence_electron in orbital_electrons:
                            for electron1 in range(len(orbital_electrons[valence_electron])):
                                for electron2 in range(len(orbital_electrons[valence_electron])):
                                    if electron1 != electron2:
                                        bond_matrix[electron1 + position, electron2 + position] = 1
                            position += len(orbital_electrons[valence_electron])
                        for index in range(size_matrix):
                            count_bond_matrix[index, index] = int(sum(bond_matrix[index, :]))
                    for number in max_bond:
                        if eem:
                            if yes_type:
                                elements_count[(elements[number - 1], max_bond[number])] += 1
                            else:
                                elements_count[elements[number - 1]] += 1
                            atoms.append(Atom(number, elements[number - 1], max_bond[number], coordinate[number - 1]))
                        if mgchm:
                            bond = str(max_bond[number]) + "|" + str(int(count_bond_matrix[number - 1, number - 1]))
                            atoms.append(Atom(number, elements[number - 1], bond))
                    while True:
                        line = fh.readline()
                        if "$$$$" in line:
                            if eem:
                                count_bond_matrix = bond_matrix = False
                            else:
                                elements_count = False
                            if ogchm:
                                count_atoms = size_matrix
                            molecules.append(Molecule(name, count_atoms, atoms, elements_count, count_bond_matrix,
                                                      bond_matrix))
                            break
        except IOError:
            print("Wrong file for molecules set! Try another file than {}".format(filename))
            sys.exit(1)

    def load_parameters(self, file_parameters):
        parameters_data, yes_type = [], False
        try:
            with open(file_parameters, "r") as fp:
                parameters = []
                for line in fp:
                    if "Kappa=" in line:
                        kappa = float(line[line.index("Kappa") + len("Kappa=\""):-3])
                    if "<Element" in line:
                        element = line[line.index("Name") + len("Name=\""):-3].strip()
                    if "<Bond" in line:
                        element_parameters = []
                        if "Type" in line:
                            yes_type = True
                            type_bond = int(line[line.index("Type") + len("Type=\"")])
                        else:
                            type_bond = 1
                        parameter_a = int(line.index("A=") + len("A=\""))
                        parameter_b = int(line.index("B=") + len("B=\""))
                        element_parameters.append((float(line[parameter_a:parameter_a + 6]),
                                                   float(line[parameter_b:parameter_b + 6])))
                        parameters.append((element, type_bond, element_parameters))
            parameters_data.append((kappa, yes_type, parameters))
            parameter = parameters_data[0]
            self.parameters = parameter
            print("Load parameters for elements from {}".format(file_parameters))
        except IOError:
            print("Wrong file for parameters! Try another file than").format(file_parameters)
            sys.exit(2)

    def __str__(self):
        return str("{}".format(self.molecules))


def get_electronegativity_from_periodic_table(elements):
    periodic_table = {}
    for element in elements:
        with open("data/Periodic Table of Elements.csv", "r", encoding="latin-1") as ftp:
            for line in ftp:
                if ("," + element + ",") in line:
                    periodic_table[element] = float(line[[m.start() for m in re.finditer(r",", line)][10] + 1:[
                        m.start() for m in re.finditer(r",", line)][11]])
                    break
    return periodic_table


def get_orbital_electrons(elements):
    matrix, orbital_electrons, ionization_potential = 0, Counter(), {}
    for x, element in enumerate(elements):
        x += 1
        with open("data/Periodic Table of Elements.csv", "r", encoding="latin-1") as ftp:
            for line in ftp:
                if ("," + element + ",") in line:
                    number = int(line[0:[m.start() for m in re.finditer(r",", line)][0]])
                    if number < 3:
                        valence_number = int(line[[m.start() for m in re.finditer(r",", line)][-3] + 3:[
                            m.start() for m in re.finditer(r",", line)][-2]])
                    else:
                        valence_number = 0
                        valence_text = line[[m.start() for m in re.finditer(r",", line)][-3] + 5:[
                            m.start() for m in re.finditer(r",", line)][-2]]
                        if len(valence_text) > 8:
                            if len(valence_text) > 10:
                                valence_text = valence_text[-8:]
                                if len(valence_text) > 8:
                                    valence_text = valence_text[-1]
                                    valence_number = int(valence_text[-1])
                            else:
                                valence_text = valence_text[-1]
                                valence_number = int(valence_text[-1])
                                break
                        maximum = int((len(valence_text)) / 4)
                        for i in range(maximum):
                            number = valence_text[3:5].strip()
                            valence_number += int(number)
                            valence_text = valence_text[3 + len(number):]
                    orbital_electrons[x] = [i for i in range(valence_number)]
                    matrix += valence_number
                    break
    return matrix, orbital_electrons

def get_electronnegativity_and_hardness(state_text, element):
    table_electronegativity, table_hardness = Counter(), Counter()
    with open("data/electronegativity_hardness.csv", "r", encoding="latin-1") as feh:
        for line in feh:
            if (element + ",") in line:
                if set(state_text) == set((line[[m.start() for m in re.finditer(r",", line)][0] + 1:[
                            m.start() for m in re.finditer(r",", line)][1]]).split(" ")):
                    table_electronegativity[element, line[[m.start() for m in re.finditer(r",", line)][1] + 1:[
                                m.start() for m in re.finditer(r",", line)][2]]] = float(
                        line[[m.start() for m in re.finditer(r",", line)][2] + 1:[
                                m.start() for m in re.finditer(r",", line)][3]])
                    table_hardness[element, line[[m.start() for m in re.finditer(r",", line)][1] + 1:[
                                m.start() for m in re.finditer(r",", line)][2]]] = float(
                        line[[m.start() for m in re.finditer(r",", line)][3] + 1:])
    return table_electronegativity, table_hardness
