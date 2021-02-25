# ghostAgents.py
# --------------
# Licensing Information:  You are free to use or extend these projects for
# educational purposes provided that (1) you do not distribute or publish
# solutions, (2) you retain this notice, and (3) you provide clear
# attribution to UC Berkeley, including a link to http://ai.berkeley.edu.
# 
# Attribution Information: The Pacman AI projects were developed at UC Berkeley.
# The core projects and autograders were primarily created by John DeNero
# (denero@cs.berkeley.edu) and Dan Klein (klein@cs.berkeley.edu).
# Student side autograding was added by Brad Miller, Nick Hay, and
# Pieter Abbeel (pabbeel@cs.berkeley.edu).


from game import Agent
from game import Actions
from game import Directions
import random
from util import manhattanDistance
import util

class GhostAgent( Agent ):
    def __init__( self, index ):
        self.index = index

    def getAction( self, state ):
        dist = self.getDistribution(state)
        if len(dist) == 0:
            return Directions.STOP
        else:
            return util.chooseFromDistribution( dist )

    def getDistribution(self, state):
        "Returns a Counter encoding a distribution over actions from the provided state."
        util.raiseNotDefined()

class RandomGhost( GhostAgent ):
    "A ghost that chooses a legal action uniformly at random."
    def getDistribution( self, state ):
        dist = util.Counter()
        for a in state.getLegalActions( self.index ): dist[a] = 1.0
        dist.normalize()
        return dist

class DirectionalGhost( GhostAgent ):
    "A ghost that prefers to rush Pacman, or flee when scared."
    def __init__( self, index, prob_attack=0.8, prob_scaredFlee=0.8 ):
        self.index = index
        self.prob_attack = prob_attack
        self.prob_scaredFlee = prob_scaredFlee

    def getDistribution( self, state ):
        # Read variables from state
        ghostState = state.getGhostState( self.index )
        legalActions = state.getLegalActions( self.index )
        pos = state.getGhostPosition( self.index )
        isScared = ghostState.scaredTimer > 0

        speed = 1
        if isScared: speed = 0.5

        actionVectors = [Actions.directionToVector( a, speed ) for a in legalActions]
        newPositions = [( pos[0]+a[0], pos[1]+a[1] ) for a in actionVectors]
        pacmanPosition = state.getPacmanPosition()

        # Select best actions given the state
        distancesToPacman = [manhattanDistance( pos, pacmanPosition ) for pos in newPositions]
        if isScared:
            bestScore = max( distancesToPacman )
            bestProb = self.prob_scaredFlee
        else:
            bestScore = min( distancesToPacman )
            bestProb = self.prob_attack
        bestActions = [action for action, distance in zip( legalActions, distancesToPacman ) if distance == bestScore]

        # Construct distribution
        dist = util.Counter()
        for a in bestActions: dist[a] = bestProb / len(bestActions)
        for a in legalActions: dist[a] += ( 1-bestProb ) / len(legalActions)
        dist.normalize()
        return dist


class AuctionSystem(object):
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(AuctionSystem, cls).__new__(cls)
            cls._instance.bidqueue = None
            cls._instance.bidwinner = None
            print "new instance"
        return cls._instance
    
    def __init__(self):
        #self.bidqueue = None
        #self.bidwinner = None
        pass
    
    def startAuction(self):
        self.bidqueue = util.PriorityQueue()
    
    def addBid(self, bidder, bid):
        if self.bidqueue is not None:
            self.bidqueue.push(bidder, bid)
    
    def endAuction(self):
        self.bidwinner = self.bidqueue.pop() # lowest bid wins
        self.bidqueue = None
    
    def getWinner(self):
        return self.bidwinner
    
    def isActive(self):
        return self.bidqueue is not None



auctioneer = None

class AuctionAgent(GhostAgent):
    def __init__(self, index, loiter_distance=5):
        self.index = index
        global auctioneer
        auctioneer = AuctionSystem()
        self.loiter_distance = loiter_distance
        self.isLoitering = False
        self.loiterPath = []


    def getAction(self, state):
        if len(self.loiterPath) <= 1: self.isLoitering = False

        if auctioneer.bidqueue is None:
            auctioneer.startAuction()
        
        auctioneer.addBid(self, manhattanDistance(state.getGhostPosition(self.index), state.getPacmanPosition())) # bids the current manhattan distance

        if (auctioneer.bidqueue.count >= state.getNumAgents()-1):
            auctioneer.endAuction()
        
        if auctioneer.getWinner() is self:
            self.isLoitering = False
            pathToPacman = self.aStar(state.getGhostPosition(self.index), state.getPacmanPosition(), state)
            return Actions.vectorToDirection((pathToPacman[1][0]-pathToPacman[0][0], pathToPacman[1][1]-pathToPacman[0][1]))
        else:
            if not self.isLoitering:
                currentPos = state.getGhostPosition(self.index)
                currentPos = (int(currentPos[0]), int(currentPos[1]))
                possiblePositions = [(self.loiter_distance*x+currentPos[0], self.loiter_distance*y+currentPos[1]) for x,y in Actions._directions.values() if (x,y) != (0,0)]
                loiterPos = random.choice(possiblePositions)
                for position in possiblePositions:
                    if position[0] < state.getWalls().width and position[1] < state.getWalls().height and state.getWalls()[position[0]][position[1]] == False and position[0] >= 0 and position[1] >= 0:
                        loiterPos = position
                assert loiterPos is not None
                print "loiterpos=" + str(loiterPos) + "Currentpos" + str(currentPos)
                path = self.aStar(currentPos, loiterPos, state)
                print path
                self.loiterPath = path + path[::-1]
                self.isLoitering = True
            print len(self.loiterPath)
            nextAction = Actions.vectorToDirection((self.loiterPath[1][0]-self.loiterPath[0][0], self.loiterPath[1][1]-self.loiterPath[0][1]))
            self.loiterPath.pop(0)
            print nextAction
            return nextAction




    def aStar(self, pos1, pos2, state):
        openList = []
        closedList = []
        f = {}
        g = {}
        parent = {}
        openList.append(pos1)
        f[pos1] = 0
        g[pos1] = 0

        while openList:
            #pop current pos
            currentNode = openList[0]
            for node in openList:
                if f[node] < f [currentNode]:
                    currentNode = node
            
            openList.remove(currentNode)
            closedList.append(currentNode)

            if currentNode == pos2:
                backwardPath = []
                node = currentNode
                while node is not None:
                    backwardPath.append(node)
                    try:
                        node = parent[node]
                    except KeyError:
                        break
                return backwardPath[::-1]

            nextNodes = Actions.getLegalNeighbors(currentNode, state.getWalls())

            for node in nextNodes:
                if node in closedList: 
                    continue
                
                g_ = g[currentNode] + 1
                h_ = manhattanDistance(node, pos2)
                f_ = g_ + h_

                if node in openList:
                    if g_ < g[node]:
                        g[node] = g_
                        parent[node] = currentNode
                        f[node] = f_
                else:
                    g[node] = g_    
                    parent[node] = currentNode
                    f[node] = f_
                    openList.append(node)


