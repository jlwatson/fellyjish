from topology import generate_topology
import pprint
from collections import Counter
import sys
import numpy as np
import pickle

def bfs(start, end, link_map):
    all_paths = {'max': sys.maxint}
    queue = [[start]]

    visited = set()
    while len(queue) > 0:
        path = queue.pop()
        if len(path) >= all_paths['max']:
            continue
        node = path[-1]
        if node not in visited:
            neighbors = link_map[node]
            for n in neighbors:
                new_path = list(path)
                new_path.append(n)
                
                if n == end:
                    l = len(new_path)
                    if l not in all_paths:
                        all_paths[l] = []
                    all_paths[l].append(new_path)
                    if len(all_paths[l]) == k and l < all_paths['max']:
                        all_paths['max'] = l
                queue.append(new_path)
            visited.add(node)
    return all_paths

def generate_paths(start, end, link_map, visited, curr_path, all_paths, k):
    if len(curr_path) >= all_paths['max']:
        return

    if start == end:
        l = len(curr_path)
        if l not in all_paths:
            all_paths[l] = []
        all_paths[l].append(list(curr_path))
        if len(all_paths[l]) == k and l < all_paths['max']:
            # print 'updating max to ' + str(l)
            all_paths['max'] = l
        return

    #visited.add(start)
    neighbors = link_map[start]
    for n in neighbors:
        if n not in curr_path:
            curr_path.append(n)
            generate_paths(n, end, link_map, visited, curr_path, all_paths, k)
            curr_path.pop()
    #visited.remove(start)


def dfs_paths(graph, start, goal, k):
    path_length_map = Counter()
    max_len = sys.maxint
    stack = [(start, [start])]

    paths = {}
    while len(stack) > 0:
        (vertex, path) = stack.pop()
        if len(path) >= max_len:
            continue
        for n in graph[vertex]:
            if n in path:
                continue
            if n == goal:
                path_len = len(path) + 1
                final_path = path + [n]
                if len(final_path) not in paths:
                    paths[len(final_path)] = []
                paths[len(final_path)].append(final_path)
                if len(paths[len(final_path)]) == k and len(final_path) < max_len:
                    max_len = len(final_path)

                # path_length_map[len(path) + 1] += 1
                # if path_length_map[len(path) + 1] == k and len(path) + 1 < max_len:
                #     max_len = len(path) + 1

                #paths.append([path + [n]])

            else:
                stack.append((n, path + [n]))

    return paths, max_len


#count for k = 8 and k = 64, using this configuration
#adjust so that multiple hosts can be for one switch, basically map hosts to corresponding switch, then use below algorithm
if __name__ == '__main__':
    n_servers = 138 * 2
    n_switches = 138 * 2
    n_ports = 12
    k = 64


    topo_map = generate_topology(n_servers=n_servers, n_switches=n_switches, n_ports=n_ports, debug=True)
    link_map = topo_map['link_map']
    print len(topo_map['link_pairs'])
    #pprint.pprint(topo_map)
    link_path_counts = Counter()
    n_servers = 686
    perm = np.random.permutation(np.arange(n_servers))
    
    for start_host in range(n_servers):
        end_host = perm[start_host]

        #map host to switch
        start_switch = start_host % n_switches
        end_switch = end_host % n_switches

        all_paths = {'max': 30}
        generate_paths(start_switch, end_switch, link_map, set(), [start_switch], all_paths, k)
        if all_paths['max'] in all_paths:
            min_length_paths = all_paths[all_paths['max']]
        else:
            continue

        distinct = set()

        for path in min_length_paths:
            for i in range(len(path) - 1):
                distinct.add((path[i], path[i + 1]))
                
                # if path[i] < path[i + 1]:
                    
                # else:
                #     link_path_counts[(path[i + 1], path[i])] += 1

        for link in distinct:
            link_path_counts[link] += 1
        print "all neighbors of " + str(start_host) + " are done"
        print link_path_counts

            
    with open('link_path_counts.pickle', 'wb') as f:
        pickle.dump(link_path_counts, f)




        # all_paths = bfs(start_host, end_host, link_map)
            # print all_paths
            # print all_paths['max']
            # print "the shortest path length between " + str(start_host) + " and " + str(end_host) + " with " + str(k) + " paths is " + str(all_paths['max'])
            # print "the paths are " + str(all_paths[all_paths['max']])
            # paths, path_length = dfs_paths(link_map, start_host, end_host, k)
            
            # print "number of paths between host " + str(start_host) + " and host " + str(end_host) + " is " + str(len(paths))
        # 
            # all_paths = []
            # generate_paths(start_host, end_host, link_map, set(), [], all_paths)

    
