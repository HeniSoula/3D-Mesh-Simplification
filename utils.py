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

def find_neighboors(model, vertex_index, r):
    neighboors = []
    for face in model.faces:

    return neighboors

def edge_collapse(model, vertex_index):
    
