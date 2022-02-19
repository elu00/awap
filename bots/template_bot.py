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

    # Helper functions
    def make_2d_array(self, val):
        return [[val for _ in range(self.MAP_HEIGHT)] for _ in range(self.MAP_WIDTH)]
    def inside(self, x, y):
        return 0 <= x and x < self.MAP_WIDTH and 0 <= y and y < self.MAP_HEIGHT
    def other_team(self, team):
        return Team.BLUE if team == Team.RED else Team.BLUE

    # returns conn comp from a team's structure
    def grow(self, map, st):
        Q = [(st.x, st.y)]
        vis = self.make_2d_array(False)
        vis[st.x][st.y] = True
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
            #Could be better
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

    def evaluate(self, x, y, map, served):
        d_util = 0

        for dx,dy in self.tower_reach:
            nx, ny = x + dx, y + dy
            if self.inside(nx,ny) and served[nx][ny] == 0:
                d_util += map[nx][ny].population

        return d_util
    
    def row_col(self, map, parents, dist, player_info):
        opp = []
        for x,y in P(range(self.MAP_WIDTH), range(self.MAP_HEIGHT)):
            st = map[x][y].structure
            if st is not None and st.team == self.opp(player_info.team):
                opp.append((x,y))

        X = set([x for x,y in opp])
        Y = set([y for x,y in opp])

        total_pop = 0
        pop_x = [0] * self.MAP_WIDTH
        pop_y = [0] * self.MAP_HEIGHT
        for x,y in P(range(self.MAP_WIDTH), range(self.MAP_HEIGHT)):
            total_pop += map[x][y].population
            pop_x[x] += map[x][y].population
            pop_y[y] += map[x][y].population

        # 3 magic number so no OOB
        for x in range(3, self.MAP_WIDTH-3):
            if x < min(X):
                if sum(pop_x[0:x-1]) > total_pop / 2:
                    #build wall
                    return

            if x > max(X):
                if sum(pop_x[x+2:]) > total_pop / 2:
                    #build wall
                    return




    def play_turn(self, turn_num, map, player_info):
        self.turn = turn_num
        self.MAP_WIDTH = len(map)
        self.MAP_HEIGHT = len(map[0])
        
        self.box_them(map, player_info)

        # start of DIJKSTRA CODE
        dist = self.make_2d_array(float("inf"))
        parents = self.make_2d_array(-1)

        queue = []
        # find tiles on my team
        for x,y in P(range(self.MAP_WIDTH),range(self.MAP_HEIGHT)):
            st = map[x][y].structure
            # check the tile is not empty
            if st is not None and st.team == player_info.team:
                dist[x][y] = 0
                queue.append((0,(x,y)))

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
        # END OF DIJKSTRA
        # player_info.money -= self.row_col(map, parents, dist, player_info)

        towers = []
        for x,y in P(range(self.MAP_WIDTH),range(self.MAP_HEIGHT)):
            st = map[x][y].structure
            if st is not None and st.team == player_info.team:
                if st.type == StructureType.TOWER:
                    towers.append(st)
        
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
        poss = []
        for x,y in P(range(self.MAP_WIDTH), range(self.MAP_HEIGHT)):
            # not owned by us or opponent and reachable
            if dist[x][y] > 0 and dist[x][y] < 10000000:
                d_util = self.evaluate(x, y, map, served)
                cost = dist[x][y] + 240 * map[x][y].passability

                curval = d_util / cost
                if curval > 0:
                    heappush(poss, (-1, -curval, -cost, (x, y), d_util))


                block = 0
                
                # finds potential blocks
                for dx in range(-2, 3):
                    for dy in range(-2, 3):
                        if abs(dx) + abs(dy) == 2:
                            if self.inside(x + dx, y + dy) and map[x + dx][y + dy].population > 0:
                                block += map[x + dx][y + dy].population

                if block:
                    heappush(poss, (0, -block/cost, -cost, (x, y), d_util))

        svalue = -1
        skips = 0

        ct = 0

        mle = player_info.money
        bt = 123

        n = self.MAP_HEIGHT * self.MAP_WIDTH
        discount_factor = 0
        if n < 1000: discount_factor = 0.9
        elif n > 4000: discount_factor = 0.5
        else: discount_factor = 0.5 + 0.4 * (n - 1000) / 3000

        #print(poss[0])
        
        while poss:
            typ, nvalue, ncost, best, util = heappop(poss)
            cost = -ncost
            value = -nvalue

            bt = min(bt, typ)

            #if typ == 0:
            #    print('HI0', bt)

            if bt != typ:
                break

            #if typ == 0:
            #   print('HI')

            if typ == -1:
                d_util = self.evaluate(best[0], best[1], map, served)
                if util != d_util:
                    print(best, util, d_util)
                    heappush(poss, (typ, curval, -cost, best, d_util))
                    continue
                
                if mle < cost:
                    skips += 1
                    if svalue == -1 and (cost - mle) < 5 * (100 + player_info.utility):
                        svalue = value
                    #print('SKIP', cost, value)
                    continue

                if value < svalue * discount_factor or value <= 0:
                    #print('BREAK')
                    break

            if mle < cost:
                continue

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

            if typ == -1:
                path = path[::-1]
                for x,y in path[:-1]:
                    st = map[xb][yb].structure
                    if st == None:
                        self.build(StructureType.ROAD, x, y)
                        mle -= 10 * map[x][y].passability
                    else:
                        print('UM')
                tx,ty = path[-1]

                assert (tx, ty) == (xb, yb)
                assert map[tx][ty].structure == None
                
                ct += 1
                self.build(StructureType.TOWER, tx, ty)
                mle -= 250 * map[tx][ty].passability
            else:
                #print('HI2')
                path = path[::-1]
                for x,y in path:
                    st = map[xb][yb].structure
                    if st == None:
                        self.build(StructureType.ROAD, x, y)
                        mle -= 10 * map[x][y].passability
                    else:
                        print('UM')

            assert mle >= 0
            #assert map[tx][ty].structure != None
            
        if ct > 1:
            print(ct)

        return
