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


    # use rectangle of each CC
    def cost_to_box(self, map, player_info):
        
        return 

    def grow(self, map, gen):
        team = gen.team
        Q = []
        vis = [[-1]]


    #calculates cost to box them and will do so if can afford
    def box_them(self, map, player_info):
        #find components of opponent
        opp_gens = []
        for x,y in P(range(self.MAP_WIDTH), range(self.MAP_HEIGHT)):
            if map[x][y].st is not None and map[x][y].st.type == StructureType.GENERATOR:
                opp_gens.append(map[x][y].st)
        
        for opp_gen in opp_gens:
            self.grow(map, opp_gen)




        return

    def evaluate(self, x, y, map, served):
        d_util = 0

        def inside(x,y):
            return 0 <= x and x < self.MAP_WIDTH and 0 <= y and y < self.MAP_HEIGHT
        
        for dx,dy in self.tower_reach:
            nx, ny = x + dx, y + dy
            if inside(nx,ny) and served[nx][ny] == 0:
                d_util += map[nx][ny].population

        return d_util
        

    def play_turn(self, turn_num, map, player_info):
        self.turn = turn_num
        # bid 0 every turn
        self.set_bid(0)
        self.MAP_WIDTH = len(map)
        self.MAP_HEIGHT = len(map[0])

        def inside(x,y):
            return 0 <= x and x < self.MAP_WIDTH and 0 <= y and y < self.MAP_HEIGHT

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
            for dx, dy in self.tower_reach:
                nx, ny = x + dx, y + dy
                if inside(nx,ny):
                    served[nx][ny] = 1

        #TODO: make evaluation better take into account current money
        #      and if we have to wait for awhile
        
        #find best location to go to and build
        poss = []
        for x,y in P(range(self.MAP_WIDTH), range(self.MAP_HEIGHT)):
            # not owned by us or opponent and reachable
            if dist[x][y] > 0 and dist[x][y] < 10000000:
                d_util = self.evaluate(x, y, map, served)
                cost = dist[x][y] + 240 * map[x][y].passability

                curval = d_util / cost
                heappush(poss, (-curval, -cost, (x, y), d_util))
        poss.sort()

        svalue = -1
        skips = 0

        while poss:
            nvalue, ncost, best, util = heappop(poss)
            cost = -ncost
            value = -nvalue

            '''d_util = self.evaluate(best[0], best[1], map, served)
            if util != d_util:
                print(best, util, d_util)
                heappush(poss, (curval, -cost, best, d_util))
                continue'''

            #print('HI')    

            if player_info.money < cost:
                skips += 1
                if svalue == -1:
                    svalue = value
                #print('SKIP', cost, value)
                continue

            if value < svalue / 2 and skips > 10 or value <= 0:
                #print('BREAK')
                break

            xb, yb = best
            st = map[xb][yb].structure
            if st != None:
                #print('Built')
                continue
            
            path = [best]
            while True:
                x,y = path[-1]
                px,py = parents[x][y]
                if dist[px][py] == 0: break
                path.append((px,py))

            path = path[::-1]
            for x,y in path[:-1]:
                st = map[xb][yb].structure
                if st == None:
                    self.build(StructureType.ROAD, x, y)
                else:
                    print('UM')
            tx,ty = path[-1]
            self.build(StructureType.TOWER, tx, ty)

        return
