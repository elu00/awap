import sys

import random
from heapq import heappop, heappush
from itertools import product as P

from src.player import *
from src.structure import *
from src.game_constants import GameConstants as GC


class MyPlayer(Player):
    def __init__(self):
        print("Init")
        self.turn = 0
        self.tower_reach = []
        for x,y in P(range(-2,3), repeat = 2):
            if abs(x) + abs(y) <= 2:
                self.tower_reach.append((x,y))

        return

    def make_2d_array(self, val):
        return [[val for _ in range(self.MAP_HEIGHT)] for _ in range(self.MAP_WIDTH)]
    def inside(self, x, y):
        return 0 <= x and x < self.MAP_WIDTH and 0 <= y and y < self.MAP_HEIGHT

    # use rectangle of each CC
    def cost_to_box(self, map, player_info):
        
        return 

    # returns conn comp from a team's structure
    def grow(self, map, st):
        Q = [(st.x, st.y)]
        vis = self.make_2d_array(False)
        while len(Q) > 0:
            x,y = Q[-1]
            Q.pop()
            for dx, dy in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
                (nx, ny) = (x + dx, y + dy)
                if self.inside(nx,ny) and (not vis[nx][ny]):
                    if map[nx][ny].structure is not None and map[nx][ny].structure.team == st.team:
                        vis[nx][ny] = True
                        Q.append((nx,ny))
        comp = []
        for x,y in P(range(self.MAP_WIDTH), range(self.MAP_HEIGHT)):
            if vis[x][y]:
                comp.append((x,y))
        return comp

    #calculates cost to box them
    #returns list of corresponding borders of each generator/component
    def box_them(self, map, player_info):
        #find components of opponent
        opp_gens = []
        for x,y in P(range(self.MAP_WIDTH), range(self.MAP_HEIGHT)):
            st = map[x][y].structure
            if (st is not None) and st.type == StructureType.GENERATOR:
                if st.team != player_info.team:
                    opp_gens.append(map[x][y].structure)
        
        comps = []
        for opp_gen in opp_gens:
            comps.append(self.grow(map, opp_gen))
        comps = list(set([tuple(set(x)) for x in comps]))
        comps = [list(x) for x in comps]

        def get_road_cost(x,y):
            if self.inside(x,y): return map[x][y].passability * 10
            else: return 0

        cost = 0
        borders = []
        for comp in comps:
            border = []
            X = set([x for x,y in comp])
            Y = set([y for x,y in comp])
            x1, x2 = min(X) - 1, max(X) + 1
            y1, y2 = min(Y) - 1, max(Y) + 1
            for x,y in P(range(x1,x2 +1), range(y1, y2 + 1)):
                if x not in set([x1,x2]) and y not in set([y1,y2]): continue
                cost += get_road_cost(x,y)
                border.append((x,y))
            border.append(border)
        return cost, borders

    def play_turn(self, turn_num, map, player_info):
        self.turn = turn_num
        self.MAP_WIDTH = len(map)
        self.MAP_HEIGHT = len(map[0])
        
        self.box_them(map, player_info)


        dist = [[float("inf")] * self.MAP_HEIGHT for _ in range(self.MAP_WIDTH)]
        parents = [[-1] * self.MAP_HEIGHT for _ in range(self.MAP_WIDTH)]

        queue = []
        # find tiles on my team
        towers = []
        for x in range(self.MAP_WIDTH):
            for y in range(self.MAP_HEIGHT):
                st = map[x][y].structure
                # check the tile is not empty
                if st is not None:
                    # check the structure on the tile is on my team
                    if st.team == player_info.team:
                        dist[x][y] = 0
                        queue.append((0,(x,y)))
                        if st.type == StructureType.TOWER:
                            towers.append(st)

        while queue:
            path_len, (x,y) = heappop(queue)
            if path_len == dist[x][y]:
                for dx, dy in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
                    (nx, ny) = (x + dx, y + dy)
                    if not self.inside(nx,ny): continue
                    st = map[nx][ny].structure
                    if st is None:
                        edge_len = map[nx][ny].passability * 10
                        if edge_len + path_len < dist[nx][ny]:
                            dist[nx][ny], parents[nx][ny] = edge_len + path_len, (x,y)
                            heappush(queue, (edge_len + path_len, (nx,ny)))
        
        served = [[0] * self.MAP_HEIGHT for _ in range(self.MAP_WIDTH)]
        for tower in towers:
            x,y = tower.x, tower.y
            for dx, dy in self.tower_reach:
                nx, ny = x + dx, y + dy
                if self.inside(nx,ny):
                    served[nx][ny] = 1

        #TODO: make evaluation better take into account current money
        #      and if we have to wait for awhile
        
        #find best location to go to and build
        best, value = (0,0), 0
        for x,y in P(range(self.MAP_WIDTH), range(self.MAP_HEIGHT)):
            # not owned by us or opponent and reachable
            if dist[x][y] > 0 and dist[x][y] < 10000000:
                d_util = 0
                for dx,dy in self.tower_reach:
                    nx, ny = x + dx, y + dy
                    if self.inside(nx,ny) and served[nx][ny] == 0:
                        d_util += map[nx][ny].population
                cost = dist[x][y] + 240 * map[x][y].passability

                curval = d_util / cost
                if curval > value: 
                    value = curval
                    best = (x,y)

        #build it
        if value > 0:
            path = [best]
            while True:
                x,y = path[-1]
                px,py = parents[x][y]
                if dist[px][py] == 0: break
                path.append((px,py))

            path = path[::-1]
            for x,y in path[:-1]:
                self.build(StructureType.ROAD, x, y)
            tx,ty = path[-1]
            self.build(StructureType.TOWER, tx, ty)
        else:
            #box them out mf
            #TODO
            return

        return