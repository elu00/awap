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

        return


    def play_turn(self, turn_num, map, player_info):
        # bid 0 every turn
        self.set_bid(0)

        self.MAP_WIDTH = len(map)
        self.MAP_HEIGHT = len(map[0])

        def inside(x,y):
            return 0 <= x and x < self.MAP_WIDTH and 0 <= y and y < self.MAP_HEIGHT

        tower_reach = []
        for x,y in P(range(-2,3), repeat = 2):
            if abs(x) + abs(y) <= 2:
                tower_reach.append((x,y))

        n = self.MAP_HEIGHT * self.MAP_WIDTH
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
                    if not inside(nx,ny): continue
                    st = map[nx][ny].structure
                    if st is None:
                        edge_len = map[nx][ny].passability * 10
                        if edge_len + path_len < dist[nx][ny]:
                            dist[nx][ny], parents[nx][ny] = edge_len + path_len, (x,y)
                            heappush(queue, (edge_len + path_len, (nx,ny)))
        
        served = [[0] * self.MAP_HEIGHT for _ in range(self.MAP_WIDTH)]
        for tower in towers:
            x,y = tower.x, tower.y
            for dx, dy in tower_reach:
                nx, ny = x + dx, y + dy
                if inside(nx,ny):
                    served[nx][ny] = 1

        
        #find best location to go to and build
        best, value = (0,0), 0
        for x,y in P(range(self.MAP_HEIGHT), range(self.MAP_WIDTH)):
            # not owned by us or opponent and reachable
            if dist[x][y] > 0 and dist[x][y] < 10000000:
                d_util = 0
                for dx,dy in tower_reach:
                    nx, ny = x + dx, y + dy
                    if inside(nx,ny) and served[nx][ny] == 0:
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