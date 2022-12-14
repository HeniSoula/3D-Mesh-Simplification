from cmath import inf
import copy
from obja import Model, parse_file, Face
import numpy as np
import time

def compute_areas(model, faces):
    return [face.area(model.vertices) for face in faces]

def compute_face_normals(model, faces):
    return [face.normal(model.vertices) for face in faces]

def compute_vertex_normal(model, vertex_index):
    faces = find_faces(model, vertex_index)
    normals = compute_face_normals(model, faces)
    vertex_normal = np.mean(normals, axis=0)
    vertex_normal /= np.linalg.norm(vertex_normal)
    return vertex_normal

def compute_curvatures(model, vertices):
    # Compute curvature at each vertex
    curvatures = []
    for vertex_index, vertex in enumerate(vertices):
        neighbours = find_neighbours_r(model, vertex_index, 1)
        if len(neighbours) == 0:
            curvatures.append(0)
        else:
            curvature = np.zeros((3,))
            for neighbour_index in neighbours:
                neighbour = model.vertices[neighbour_index]
                curvature += vertex-neighbour/np.linalg.norm(neighbour-vertex)

            curv = np.linalg.norm(curvature)/len(neighbours)
            curvatures.append(curv)
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
    neighbours.discard(vertex_index)
    return neighbours

def find_neighbours_r(model, vertex_index, r):
    neighbours = {vertex_index}
    for _ in range(r):
        temp = neighbours.copy()
        for elt in temp:
            neighbours.update(find_neighbours(model, elt))
    neighbours.remove(vertex_index)
    return list(neighbours)

def sampling(curvatures, num):
    min_curvature = np.min(curvatures)
    max_curvature = np.max(curvatures)
    sampled = np.linspace(min_curvature, max_curvature, num)
    return sampled

def compute_vertex_area(model, vertex_index):
    faces = find_faces(model, vertex_index)
    areas = compute_areas(model, faces)
    vertex_area = np.sum(areas)/3
    return vertex_area

def saliency_map(model, mesh_curvatures, vertices, r):
    saliency = []
    for vertex_index in vertices:
        neighbours = find_neighbours_r(model, vertex_index, r)
        curv = [mesh_curvatures[neighbour] for neighbour in neighbours]
        sigmas = sampling(curv, 7)
        entropy = compute_entropy(model, sigmas, curv, neighbours)
        saliency.append(entropy)
    return saliency

def compute_entropy(model, sigmas, curv, neighbours):
    total_areas = [compute_vertex_area(model, idx) for idx in neighbours]
    total_area = np.sum(total_areas)
    entropy = 0
    for sigma in sigmas:
        areas = 0
        for i, curvature in enumerate(curv):
            if abs(sigmas[sigmas <= curvature].max() - sigma)/sigma <= 1e-3:
                neighbour_area = total_areas[i]
                areas += neighbour_area
        p = areas/total_area
        if p > 1e-8:
            entropy -= p*np.log2(p)

    return entropy

def edge_collapse(model, vertex_index, saliency):
    operations1 = []
    operations2 = []
    output = Model()
    neighbours = find_neighbours_r(model, vertex_index, 1)
    neighbour_saliencies = [saliency[neighbour] for neighbour in neighbours]
    remove_index = neighbours[np.argmin(neighbour_saliencies)]

    output.vertices = copy.copy(model.vertices)
    vtx = (model.vertices[vertex_index] + model.vertices[remove_index])/2
    output.vertices.append(vtx)
    
    for k, face in enumerate(model.faces):
        indices = [face.a, face.b, face.c]
        indices2 = [face.a, face.b, face.c]
        if ((vertex_index in indices) and (remove_index in indices)):
            # print("index of removed face = ", k+1)
            operations1.append("af " + " " + str(k+1) + " " + str(face.a+1) + " " + str(face.b+1) + " " + str(face.c+1))
            continue
        for i in range(3):
            if (indices[i] == remove_index) or (indices[i] == vertex_index):
                indices[i] = len(output.vertices) - 1
                operations2.append("efv " + str(k+1) + " " + str(i+1) + " " + str(indices2[i]+1))

        output.faces.append(Face(indices[0], indices[1], indices[2]))

    operations1.reverse()
    operations2.reverse()
    operations = operations2 + operations1

    return output, remove_index, operations


# Testing
path = "example\\suzanne.obj"
model = parse_file(path)

# Preprocessing
# Remove vertices that have no neighbours
temp = []
for i in range(len(model.vertices)):
    if len(find_neighbours_r(model, i, 1)) > 0:
        temp.append(model.vertices[i])
model.vertices = temp


ops = []
nb_edge_collapse = 250
r = 2
mesh_curvatures = compute_curvatures(model, model.vertices)
saliency = saliency_map(model, mesh_curvatures, range(len(model.vertices)), r)
for i in range(nb_edge_collapse):
    vertex_index = np.argmin(saliency)
    if saliency[vertex_index] == +inf:
        break
    model, remove_index, operations = edge_collapse(model, vertex_index, saliency)
    saliency.append(0)
    ops.append(operations)
    mesh_curvatures = compute_curvatures(model, model.vertices)
    local_vertices = find_neighbours_r(model, len(model.vertices)-1, r)
    if len(local_vertices) != 0:
        local_vertices.append(len(model.vertices)-1)
        local_saliency = saliency_map(model, mesh_curvatures, local_vertices, r)
        for cpt, idx in enumerate(local_vertices):
            saliency[idx] = local_saliency[cpt]
    for j in range(len(model.vertices)):
        if len(find_neighbours_r(model, j, 1)) == 0:
            saliency[j] = +inf

ops = [item for sublist in ops for item in sublist]
ops.reverse()
# print(ops)

with open(".\\results\\suzanne.obja", 'w') as f:
    for i, vertex in enumerate(model.vertices):
        f.write("v")
        f.write(" ")
        f.write(str(vertex[0]))
        f.write(" ")
        f.write(str(vertex[1]))
        f.write(" ")
        f.write(str(vertex[2]))
        f.write("\n")
    
    for face in model.faces:
        f.write("f")
        f.write(" ")
        f.write(str(face.a + 1))
        f.write(" ")
        f.write(str(face.b + 1))
        f.write(" ")
        f.write(str(face.c + 1))
        f.write("\n")
    
    for op in ops:
        f.write(op)
        f.write("\n")
