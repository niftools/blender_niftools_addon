#adapted from https://raw.githubusercontent.com/JuhaW/NodeArrange/master/__init__.py

from collections import OrderedDict
from itertools import repeat

class values():
	average_y = 0
	x_last = 0
	margin_x = 300
	mat_name = ""
	margin_y = 200
	
def nodes_iterate(ntree, nodeoutput):
	
	a = [ [nodeoutput,], ]
	level = 0
		
	while a[level]:
		a.append([])
		#print ("level:",level)
		
		for node in a[level]:
			#print ("while: level:", level)
			inputlist = [i for i in node.inputs if i.is_linked]
			#print ("inputlist:", inputlist)
			if inputlist:
								
				for input in inputlist:
					for nlinks in input.links:
						#dont add parented nodes (inside frame) to list
						#if not nlinks.from_node.parent:
						node1 = nlinks.from_node
						#print ("appending node:",node1)
						a[level + 1].append(node1)
			
			else:
				pass
				#print ("no inputlist at level:", level)

		level += 1
		
	#delete last empty list
	del a[level]
	level -= 1
	
	#remove duplicate nodes at the same level, first wins
	for x, nodes in enumerate(a):
		a[x] = list(OrderedDict(zip(a[x], repeat(None))))
	#print ("Duplicate nodes removed")
	
	#remove duplicate nodes in all levels, last wins
	top = level 
	for row1 in range(top, 1, -1):
		#print ("row1:",row1, a[row1])
		for col1 in a[row1]:
			#print ("col1:",col1)
			for row2 in range(row1-1, 0, -1):
				for col2 in a[row2]:
					if col1 == col2:
						#print ("Duplicate node found:", col1)
						#print ("Delete node:", col2)
						a[row2].remove(col2)
						break

	levelmax = level + 1
	level = 0
	values.x_last = 0

	while level < levelmax:

		values.average_y = 0
		nodes = [x for x in a[level]]
		#print ("level, nodes:", level, nodes)
		nodes_arrange(ntree, nodes, level)
		
		level = level + 1

	return None

def nodes_arrange(ntree, nodelist, level):

	parents = []
	for node in nodelist:
		parents.append(node.parent)
		node.parent = None
		ntree.nodes.update()
		
		
	#print ("nodes arrange def")
	# node x positions

	widthmax = max([x.dimensions.x for x in nodelist])
	xpos = values.x_last - (widthmax + values.margin_x) if level != 0 else 0
	#print ("nodelist, xpos", nodelist,xpos)
	values.x_last = xpos

	# node y positions
	x = 0
	y = 0

	for node in nodelist:

		if node.hide:
			hidey = (node.dimensions.y / 2) - 8
			y = y - hidey
		else:
			hidey = 0

		node.location.y = y
		y = y - values.margin_y - node.dimensions.y + hidey

		node.location.x = xpos #if node.type != "FRAME" else xpos + 1200
		
	y = y + values.margin_y

	center = (0 + y) / 2
	values.average_y = center - values.average_y

	for node in nodelist:

		node.location.y -= values.average_y

	for i, node in enumerate(nodelist):
		node.parent =  parents[i]
