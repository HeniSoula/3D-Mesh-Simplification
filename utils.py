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

# def compute_curvatures(model):
#     # Compute curvature at each vertex
#     curvatures = []
#     for vertex_index, vertex in enumerate(model.vertices):
#         vertex_normal = compute_vertex_normal(model, vertex_index)

#         neighbours = find_neighbours_r(model, vertex_index, 1)
#         curvature = 0
#         for neighbour_index in neighbours:
#             neighbour = model.vertices[neighbour_index]
#             neighbour_normal = compute_vertex_normal(model, neighbour_index)
#             curvature += np.inner(neighbour_normal-vertex_normal, neighbour-vertex)/np.linalg.norm(neighbour-vertex)**2

#         curvature /= len(neighbours)
#         curvatures.append(curvature)
#     return curvatures

def compute_curvatures(model):
    # Compute curvature at each vertex
    curvatures = []
    for vertex_index, vertex in enumerate(model.vertices):

        neighbours = find_neighbours_r(model, vertex_index, 1)
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

def saliency_map(model, mesh_curvatures):
    saliency = []
    for vertex_index in range(len(model.vertices)):
        neighbours = find_neighbours_r(model, vertex_index, 1)
        curvatures = [mesh_curvatures[neighbour] for neighbour in neighbours]
        sigmas = sampling(curvatures, int(len(curvatures)/4))
        entropy = compute_entropy(model, sigmas, curvatures, neighbours)
        saliency.append(entropy)
    return saliency

def compute_entropy(model, sigmas, curvatures, neighbours):
    total_areas = [compute_vertex_area(model, idx) for idx in neighbours]
    total_area = np.sum(total_areas)
    entropy = 0
    for sigma in sigmas:
        p = 0
        areas = 0
        for i, curvature in enumerate(curvatures):
            if sigmas[sigmas <= curvature].max() == sigma:
                neighbour_area = total_areas[i]
                areas += neighbour_area
        p = areas/total_area

        entropy -= p*np.log2(p)
    return entropy

def edge_collapse(model, vertex_index, saliency):
    output = Model()
    neighbours = find_neighbours_r(model, vertex_index, 1)
    neighbour_saliencies = [saliency[neighbour] for neighbour in neighbours]
    remove_index = neighbours[np.argmin(neighbour_saliencies)]

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

    return output, remove_index


# Testing
path = "example\\bunny.obj"
model = parse_file(path)

t1 = time.time()
curvatures = compute_curvatures(model)
t2 = time.time()
print("time needed to compute curvatures : ", t2 - t1)
t3 = time.time()
saliency = saliency_map(model, curvatures)
t4 = time.time()
print("time needed to compute saliency : ", t4 - t3)

vertex_index = np.argmin(curvatures)
new_model, remove_index = edge_collapse(model, vertex_index, saliency)

print("removed index : ", remove_index)

min_curvature = np.min(curvatures)
max_curvature = np.max(curvatures)
for i in range(len(curvatures)):
    curvatures[i] = (curvatures[i]-min_curvature)/(max_curvature-min_curvature)

min_saliency = np.min(saliency)
max_saliency = np.max(saliency)
for i in range(len(saliency)):
    saliency[i] = (saliency[i]-min_saliency)/(max_saliency-min_saliency)

with open(".\\results\\bunny_result.obj", 'w') as f:
    for i, vertex in enumerate(model.vertices):
        f.write("v")
        f.write(" ")
        f.write(str(vertex[0]))
        f.write(" ")
        f.write(str(vertex[1]))
        f.write(" ")
        f.write(str(vertex[2]))
        f.write(" ")
        f.write(str(saliency[i]))
        f.write(" ")
        f.write("0")
        f.write(" ")
        f.write("0")
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
