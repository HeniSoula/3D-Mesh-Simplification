from obja import parse_file
import copy
import numpy as np

def compute_areas(model, faces):
    return [face.area(model.vertices) for face in faces]

def compute_face_normals(model, faces):
    return [face.normal(model.vertices) for face in faces]

def compute_vertex_normal(model, vertex_index):
    faces = find_faces(model, vertex_index)
    normals = compute_face_normals(model, faces)
    vertex_normal = np.mean(normals)
    return vertex_normal

def compute_curvatures(model):
    # Compute curvature at each vertex
    curvatures = []
    for vertex_index, vertex in enumerate(model.vertices):
        vertex_normal = compute_vertex_normal(model, vertex_index)

        neighbours = find_neighbours_r(model, vertex_index, 1)
        curvature = 0
        for neighbour_index in neighbours:
            neighbour = model.vertices[neighbour_index]
            neighbour_normal = compute_vertex_normal(model, neighbour_index)
            curvature += np.dot(neighbour_normal-vertex_normal, neighbour-vertex)/np.linalg.norm(neighbour-vertex)**2

        curvatures.append(curvature)
    return curvatures

def find_faces(model, vertex_index):
    faces = []
    for face in model.faces:
        indices = [face.a, face.b, face.c]
        if vertex_index in indices:
            faces.append(face)
    return faces

def find_neighbours(model, vertex_index):
    neighbours = set()
    for face in model.faces:
        indices = [face.a, face.b, face.c]
        if vertex_index in indices:
            for index in indices:
                neighbours.add(index)
    neighbours.remove(vertex_index)
    return neighbours


def find_neighbours_r(model, vertex_index, r):
    neighbours = {vertex_index}
    for _ in range(r):
        temp = neighbours.copy()
        for elt in temp:
            neighbours.update(find_neighbours(model, elt))
    neighbours.remove(vertex_index)
    return list(neighbours)


def edge_collapse(model, vertex_index):
    new_model = copy.deepcopy(model)
    neighbours = find_neighbours_r(new_model, vertex_index, 1)
    v_s = new_model.vertices[vertex_index]
    remove_index = neighbours[4]
    v_t = new_model.vertices[remove_index]

    # Removing one of the vertices
    # Au hasard pour l'instant
    del new_model.vertices[remove_index]

    # Editing the other one
    new_model.vertices[vertex_index] = (v_s + v_t)/2

    # Décaler de 1 tous les indices des faces à partir du vertex supprimé
    removed_faces = []
    temp = new_model.faces.copy()
    for face in temp:
        indices = [face.a, face.b, face.c]
        if (vertex_index in indices) and (remove_index in indices):
            removed_faces.append(face)
            new_model.faces.remove(face)
        else:
            if face.a == remove_index :
                face.a = vertex_index
            elif face.a >= remove_index:
                face.a -= 1
            if face.b == remove_index :
                face.b = vertex_index
            elif face.b >= remove_index:
                face.b -= 1
            if face.c == remove_index :
                face.c = vertex_index
            elif face.c >= remove_index:
                face.c -= 1
    
    return new_model, remove_index, removed_faces

def compute_area_vertex_simplified(model, vertex_index):
    faces = find_faces(model, vertex_index)
    areas = compute_areas(model, faces)
    vertex_area = np.sum(areas)/3
    return vertex_area

def probabilite(model, vertex_index, curvatures):
    sigma = curvatures[vertex_index]
    neighbours = find_neighbours(model, vertex_index)
    area_important = 0
    area_total = 0
    for i in range(len(neighbours)) :
        sigma_neighbour = curvatures[neighbours[i]]
        area_neighbour = compute_area_vertex_simplified(model, neighbours[i])
        area_total += area_neighbour
        if sigma == sigma_neighbour :
            area_important += area_neighbour
    return (area_important/area_total)


# Testing
path = "example\\bunny.obj"
model = parse_file(path)
vertex_index = 0
new_model, remove_index, removed_faces = edge_collapse(model, vertex_index)

print("removed index : ", remove_index)
print("removed faces : ", removed_faces)

print(150*"-")

print("first n faces BEFORE edge collapse :\n", model.faces[:7])
print("first n faces After edge collapse :\n", new_model.faces[:7])

print(150*"-")

print("faces containing remove_index BEFORE edge collapse :\n ", find_faces(model, remove_index))
print("faces containing vertex_index AFTER edge collapse :\n ", find_faces(new_model, vertex_index))

curvatures = compute_curvatures(new_model)