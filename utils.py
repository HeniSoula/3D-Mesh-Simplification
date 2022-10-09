from obja import parse_file

def compute_areas(model):
    return [face.area(model.vertices) for face in model.faces]

def compute_curvatures(model):
    # Compute curvature at each vertex
    curvatures = []
    for vertex in model.vertices:
        #TODO
        curvature = 1
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
    neighbours = find_neighbours_r(model, vertex_index, 1)
    v_s = model.vertices[vertex_index]
    remove_index = neighbours[4]
    v_t = model.vertices[remove_index]

    # Removing one of the vertices
    # Au hasard pour l'instant
    del model.vertices[remove_index]

    # Editing the other one
    model.vertices[vertex_index] = (v_s + v_t)/2

    # Décaler de 1 tous les indices des faces à partir du vertex supprimé
    removed_faces = []
    temp = model.faces.copy()
    for face in temp:
        indices = [face.a, face.b, face.c]
        if (vertex_index in indices) and (remove_index in indices):
            removed_faces.append(face)
            model.faces.remove(face)
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
    
    return model, remove_index, removed_faces

# Testing
path = "example\\bunny.obj"
model = parse_file(path)
print(model.faces[:8])
print("before : ",find_faces(model,1070))
model, remove_index, removed_faces = edge_collapse(model, 0)
print("remove_index : ",remove_index)
print(removed_faces)
print(model.faces[:8])
print("after : ",find_faces(model,0))
