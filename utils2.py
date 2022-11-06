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

def saliency_map(model, mesh_curvatures, vertices, r, i):
    saliency = []
    for vertex_index in vertices:
        neighbours = find_neighbours_r(model, vertex_index, r)
        curv = [mesh_curvatures[neighbour] for neighbour in neighbours]
        sigmas = sampling(curv, 25)
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
    output = Model()
    neighbours = find_neighbours_r(model, vertex_index, 1)
    neighbour_saliencies = [saliency[neighbour] for neighbour in neighbours]
    remove_index = neighbours[np.argmin(neighbour_saliencies)]
    decrement = vertex_index > remove_index

    for i in range(len(model.vertices)):
        if (i == vertex_index):
            output.vertices.append((model.vertices[i] + model.vertices[remove_index])/2)
        elif (i != remove_index and i != vertex_index):
            output.vertices.append(model.vertices[i])
        
    for face in model.faces:
        indices = [face.a, face.b, face.c]    
        if ((vertex_index in indices) and (remove_index in indices)):
            continue
        for i in range(3):
            if (indices[i] == remove_index):
                indices[i] = vertex_index
            if (indices[i] > remove_index):
                indices[i] -= 1    
        output.faces.append(Face(indices[0], indices[1], indices[2]))

    return output, remove_index, decrement


# Testing
path = "example\\bunny.obj"
model = parse_file(path)

# Preprocessing
# Remove vertices that have no neighbours
temp = []
for i in range(len(model.vertices)):
    if len(find_neighbours_r(model, i, 1)) > 0:
        temp.append(model.vertices[i])
model.vertices = temp


nb_edge_collapse = 1500
r = 2
t1 = time.time()
mesh_curvatures = compute_curvatures(model, model.vertices)
saliency = saliency_map(model, mesh_curvatures, range(len(model.vertices)), r, 0)
t2 = time.time()
print("time 1 : ", t2 - t1)
t3 = time.time()
for i in range(nb_edge_collapse):
    vertex_index = np.argmin(saliency)
    #new_model, remove_index, decrement = edge_collapse(model, vertex_index, saliency)
    model, remove_index, decrement = edge_collapse(model, vertex_index, saliency)
    mesh_curvatures = compute_curvatures(model, model.vertices)
    #model = copy.deepcopy(new_model)
    saliency.pop(remove_index)
    if decrement:
        vertex_index -= 1
    local_vertices = find_neighbours_r(model, vertex_index, r)
    if len(local_vertices) != 0:
        local_vertices.append(vertex_index)
        local_saliency = saliency_map(model, mesh_curvatures, local_vertices, r, i)
        for cpt, idx in enumerate(local_vertices):
            saliency[idx] = local_saliency[cpt]
    for j in range(len(model.vertices)):
        if len(find_neighbours_r(model, j, 1)) == 0:
            saliency[j] = +inf
t4 = time.time()
print("time 2 : ", t4 - t3)

# min_curvature = np.min(mesh_curvatures)
# max_curvature = np.max(mesh_curvatures)
# for i in range(len(mesh_curvatures)):
#     mesh_curvatures[i] = (mesh_curvatures[i]-min_curvature)/(max_curvature-min_curvature)

# min_saliency = np.min(saliency)
# max_saliency = np.max(saliency)
# for i in range(len(saliency)):
#     #saliency[i] = (saliency[i] - min_saliency)/(max_saliency - min_saliency)
#     saliency[i] /= max_saliency

with open(".\\results\\bunny_test.obj", 'w') as f:
    for i, vertex in enumerate(model.vertices):
        f.write("v")
        f.write(" ")
        f.write(str(vertex[0]))
        f.write(" ")
        f.write(str(vertex[1]))
        f.write(" ")
        f.write(str(vertex[2]))
        # f.write(" ")
        # f.write(str(saliency[i]))
        # f.write(" ")
        # f.write("0")
        # f.write(" ")
        # f.write("0")
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