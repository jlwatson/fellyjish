import networkx as nx
import numpy as np
from collections import Counter

num_hosts = 686
num_switches = 276
k = 14
r = 12

ecmp_ct = 1

graph = nx.generators.random_graphs.random_regular_graph(r, num_switches)
#map host to switch

end_perm = np.random.permutation(np.arange(num_hosts))

link_count = Counter()

for start_host in range(num_hosts):
	start_sw = start_host % num_switches
	end_host = end_perm[start_host]
	end_sw = end_host % num_switches
	paths = nx.shortest_simple_paths(graph, source=start_sw, target=end_sw) 
	path_length_to_path = {}
	for path in paths:
		if len(path) not in path_length_to_path:
			path_length_to_path[len(path)] = []
		path_length_to_path[len(path)].append(path)
		if len(path_length_to_path[len(path)]) == ecmp_ct:
			distinct = set()
			for chosen_path in path_length_to_path[len(path)]:
				for i in range(len(chosen_path) - 1):
					distinct.add((chosen_path[i], chosen_path[i + 1]))
			for link in distinct:
				link_count[link] += 1
			break
	print link_count


