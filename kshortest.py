from collections import defaultdict
import Queue
import random
import sys


def find_paths_between(topo_map, begin, end, k):

    path_queue = Queue.PriorityQueue()
    path_queue.put((0, [begin]))
    path_queue_size = 1

    path_counts = defaultdict(int)
    shortest_paths = []

    while path_queue_size > 0 and path_counts[end] < k:
        curr_cost, curr_path = path_queue.get()
        path_queue_size -= 1
        last = curr_path[-1]
        path_counts[last] += 1

        if last == end:
            shortest_paths.append(curr_path)
        
        if path_counts[last] <= k:
            for neighbor_idx in topo_map["link_map"][topo_map["switches"].index(last)]:
                neighbor = topo_map["switches"][neighbor_idx]
                if neighbor not in curr_path:
                    new_cost, new_path = curr_cost + 1, curr_path + [neighbor]
                    path_queue.put((new_cost, new_path)) 
                    path_queue_size += 1

    return shortest_paths


def k_shortest_paths(topo_map, k):
    '''
    `topo_map`
        hosts:      ['h1', 'h2', ...]
        switches:   ['s1', 's2', ...]
        link_map:   {'s1': ['s2', ...], 's3': ['s2', 's4', ...]}
        link_pairs: [('s1', 's2'), ('s3', 's2'), ...]
    '''

    path_collection = {}
    for i, h1 in enumerate(topo_map["hosts"]):
        for j, h2 in enumerate(topo_map["hosts"][i+1:]):
            s1, s2 = topo_map["switches"][i], topo_map["switches"][i+j+1]
            paths = find_paths_between(topo_map, s1, s2, k=k)
            path_collection[(h1, h2)] = paths
            path_collection[(h2, h1)] = [list(reversed(p)) for p in paths]

    return path_collection

