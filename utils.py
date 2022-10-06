from obja import parse_file
from math import sqrt

# Load model
path = "example\\bunny.obj"
model = parse_file(path)

# Fix radius r for neighborhood
r = 3

def compute_areas(model):
    # Compute areas of faces
    areas = []
    for face in model.faces:
        a, b, c = model.vertices[face.a], model.vertices[face.b], model.vertices[face.c]
        y_AB = b[1] - a[1]
        z_AC = c[2] - a[2]
        z_AB = b[2] - a[2]
        y_AC = c[1] - a[1]
        x_AC = c[0] - a[0]
        x_AB = b[0] - a[0]
        area = 0.5*sqrt((y_AB*z_AC - z_AB*y_AC)**2 + (z_AB*x_AC - x_AB*z_AC)**2 + (x_AB*y_AC - y_AC*x_AC)**2)
        areas.append(area)
    return areas


def compute_curvatures(model):
    # Compute curvature at each vertex
    curvatures = []
    for vertex in model.vertices:
        #TODO
        curvature = 1
        curvatures.append(curvature)
    return curvatures


def find_neighbours(model, vertex_index):
    neighbours = set()
    for face in model.faces:
        indices = [face.a, face.b, face.c]
        if vertex_index-1 in indices:
            for index in indices:
                neighbours.add(index+1)
    neighbours.remove(vertex_index)
    return neighbours


def find_neighbours_r(model, vertex_index, r):
    neighbours = {vertex_index}
    for _ in range(r):
        neighbours2 = neighbours.copy()
        for elt in neighbours2:
            temp = find_neighbours(model, elt)
            neighbours.update(temp)
    neighbours.remove(vertex_index)
    return list(neighbours)


def edge_collapse(model, vertex_index):
    neighbours = find_neighbours_r(model, vertex_index, 1)
    V_s = model.vertices[vertex_index]
    V_t = model.vertices[neighbours[0]]

    # Removing one of the vertex
    # Au hasard pour l'instant
    del model.vertices[neighbours[0]]

    # Editing the other one
    model.vertices[vertex_index][0] = (V_s[0] + V_t[0])/2
    model.vertices[vertex_index][1] = (V_s[1] + V_t[1])/2
    model.vertices[vertex_index][2] = (V_s[2] + V_t[2])/2

    # Décaler de 1 tous les indices des faces à partir du vertex supprimé
    for i in range(len(model.faces)):
        a = model.faces[i].a
        b = model.faces[i].b
        c = model.faces[i].c

        if a >= neighbours[0] :
            a = a - 1
        if b >= neighbours[0] :
            b = b - 1
        if c >= neighbours[0] :
            c = c - 1


