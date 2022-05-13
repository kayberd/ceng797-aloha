import os
import shutil
import random
from enum import Enum

import matplotlib.pyplot as plt
import networkx as nx
import threading
from time import sleep
from itertools import combinations, groupby
from math import cos, sin, atan2


from adhoccomputing.GenericModel import GenericModel
from adhoccomputing.Generics import Event, EventTypes, ConnectorTypes
from adhoccomputing.Experimentation.Topology import Topology
from adhoccomputing.Networking.LinkLayer.GenericLinkLayer import GenericLinkLayer
from adhoccomputing.Networking.LogicalChannels.GenericChannel import GenericChannel
from adhoccomputing.DistributedAlgorithms.MutualExclusion.RicartAgrawala import MutualExclusionAgrawalaComponent





SAVED_FILE_INDEX = 0
SAVING_ENABLED = False
SAVE_PATH = os.path.join(os.path.dirname(__file__), "ricartAgrawalaOut")

FPS = 24.0

EDGE_COLOR = '#7F7F7F'

PRIVILEGED_NODE_COLOR = '#FF0000'
WAITING_NODE_COLOR = '#FFFF00'
NODE_COLOR = '#00FF00'

drawnGraphNodeColors = []
drawnGraphNodeLabels = []

labelDistance = 0

class COMMAND(Enum):
    DRAW = "draw"
    REQUEST = "request"
    HELP = "help"
    SET = "set"
    GET = "get"


class ARGUMENT(Enum):
    ALL = "-all"
    TIME = "-time"
    DISTANCE = "-distance"
    REQUEST = "-request"
    REPLY = "-reply"
    PRIVILEGE = "-privilege"
    FORWARDED = "-forwarded"
    MEAN = "-mean"
    TOTAL = "-total"


def processUserCommand(userInput: str):
    try:
        splitInput = userInput.split()
        cmd = splitInput[0]
        args = []
        if len(splitInput) > 1:
            args = splitInput[1:]

        if cmd == COMMAND.REQUEST.value:
            requestCommand(args)
        elif cmd == COMMAND.DRAW.value:
            drawCommand(args)
        elif cmd == COMMAND.SET.value:
            setCommand(args)
        elif cmd == COMMAND.GET.value:
            getCommand(args)
        elif cmd == COMMAND.HELP.value:
            helpCommand()
        else:
            print(f"Unknown input: \'{userInput}\'")
    except IndexError:
        pass

def helpCommand(cmd=COMMAND.HELP):
    if cmd is COMMAND.REQUEST:
        print(f"Request:\n"
              f"\t\"{COMMAND.REQUEST.value} nodeId\"\n"
              f"\t\"{COMMAND.REQUEST.value} nodeId1 nodeId2...\"\n"
              f"\t\"{COMMAND.REQUEST.value} {ARGUMENT.ALL.value}\"")
    elif cmd is COMMAND.DRAW:
        print(f"Draw:\n"
              f"\t\"{COMMAND.DRAW.value}\"")
    elif cmd is COMMAND.SET:
        print(f"Set:\n"
              f"\t\"{COMMAND.SET.value} {ARGUMENT.TIME.value} t\"\n"
              f"\t\"{COMMAND.SET.value} {ARGUMENT.DISTANCE.value} d\"")
    elif cmd is COMMAND.GET:
        print(f"Get:\n"
              f"\t\"{COMMAND.GET.value} {ARGUMENT.TIME.value}\"\n"
              f"\t\"{COMMAND.GET.value} {ARGUMENT.DISTANCE.value}\"\n"
              f"\t\"{COMMAND.GET.value} {ARGUMENT.ALL.value}\"\n"
              f"\t\"{COMMAND.GET.value} {ARGUMENT.ALL.value} nodeId\"\n"
              f"\t\"{COMMAND.GET.value} {ARGUMENT.ALL.value} [{ARGUMENT.REQUEST.value}/{ARGUMENT.REPLY.value}/{ARGUMENT.PRIVILEGE.value}/{ARGUMENT.FORWARDED.value}]\"\n"
              f"\t\"{COMMAND.GET.value} [{ARGUMENT.REQUEST.value}/{ARGUMENT.REPLY.value}/{ARGUMENT.PRIVILEGE.value}/{ARGUMENT.FORWARDED.value}] nodeId\"\n"
              f"\t\"{COMMAND.GET.value} [{ARGUMENT.MEAN.value}/{ARGUMENT.TOTAL.value}]\"\n"
              f"\t\"{COMMAND.GET.value} [{ARGUMENT.MEAN.value}/{ARGUMENT.TOTAL.value}] [{ARGUMENT.REQUEST.value}/{ARGUMENT.REPLY.value}/{ARGUMENT.PRIVILEGE.value}/{ARGUMENT.FORWARDED.value}]\"")
    else:
        helpCommand(COMMAND.REQUEST)
        helpCommand(COMMAND.DRAW)
        helpCommand(COMMAND.SET)
        helpCommand(COMMAND.GET)

def requestCommand(args):
    allNodes = ARGUMENT.ALL.value in args
    if allNodes:
        args.remove(ARGUMENT.ALL.value)

        if len(args) == 0:
            for nodeID in topology.nodes:
                topology.nodes[nodeID].send_request()
        else:
            helpCommand(COMMAND.REQUEST)
    else:
        nodes = list()
        for arg in args:
            try:
                nodeID = int(arg)
                node = topology.nodes[nodeID]
                nodes.append(node)
            except KeyError:
                print(f"Node {nodeID} does not exist in the topology.")
            except ValueError:
                print(f"\'{arg}\' is not integer.")

        if nodes:
            for node in nodes:
                node.send_request()
        else:
            helpCommand(COMMAND.REQUEST)

def drawCommand(args):
    if len(args) == 0:
        drawGraph(True)
    else:
        helpCommand(COMMAND.DRAW)

def setCommand(args):
    global labelDistance
    setTime = ARGUMENT.TIME.value in args
    setDistance = ARGUMENT.DISTANCE.value in args

    if setTime and not setDistance:
        args.remove(ARGUMENT.TIME.value)

        if len(args) == 1:
            try:
                t = float(args[0])
                if t > 0:
                    MutualExclusionAgrawalaComponent.privilegeSleepAmount = t
                else:
                    print(f"Sleep time cannot be set to {t}, choose a value above 0!")
            except ValueError:
                print(f"\'{args[0]}\' is not float.")
        else:
            helpCommand(COMMAND.SET)
    elif setDistance and not setTime:
        args.remove(ARGUMENT.DISTANCE.value)

        if len(args) == 1:
            try:
                labelDistance = float(args[0])
                drawGraph(True)
            except ValueError:
                print(f"\'{args[0]}\' is not float.")
        else:
            helpCommand(COMMAND.SET)
    else:
        helpCommand(COMMAND.SET)

def getNodeInformation(node: MutualExclusionAgrawalaComponent, request=True, reply=True, privilege=True, forwarded=True):
    information = []

    if request:
        information.append(f"ReceivedRequests: {node.receivedRequestCount}")
        information.append(f"SentRequests: {node.sentRequestCount}")
    if reply:
        information.append(f"ReceivedReplies: {node.receivedReplyCount}")
        information.append(f"SentReplies: {node.sentReplyCount}")
    if privilege:
        information.append(f"Privileged: {node.privilegeCount}")
    if forwarded:
        information.append(f"ForwardedMessages: {node.forwardedMessageCount}")

    return f"{node.componentinstancenumber} => " + " | ".join(information)

def getCommand(args):
    global labelDistance

    isTime = ARGUMENT.TIME.value in args
    isDistance = ARGUMENT.DISTANCE.value in args

    isAll = ARGUMENT.ALL.value in args
    isMean = ARGUMENT.MEAN.value in args
    isTotal = ARGUMENT.TOTAL.value in args

    isRequest = ARGUMENT.REQUEST.value in args
    isReply = ARGUMENT.REPLY.value in args
    isPrivilege = ARGUMENT.PRIVILEGE.value in args
    isForwarded = ARGUMENT.FORWARDED.value in args
    areAnyOtherArgumentsSet = isRequest or isReply or isPrivilege or isForwarded

    if isTime:
        args.remove(ARGUMENT.TIME.value)
    if isDistance:
        args.remove(ARGUMENT.DISTANCE.value)
    if isAll:
        args.remove(ARGUMENT.ALL.value)
    if isMean:
        args.remove(ARGUMENT.MEAN.value)
    if isTotal:
        args.remove(ARGUMENT.TOTAL.value)
    if isRequest:
        args.remove(ARGUMENT.REQUEST.value)
    if isReply:
        args.remove(ARGUMENT.REPLY.value)
    if isPrivilege:
        args.remove(ARGUMENT.PRIVILEGE.value)
    if isForwarded:
        args.remove(ARGUMENT.FORWARDED.value)

    if (isTime or isDistance) and not isAll and not (isMean or isTotal):
        if len(args) == 0 and not areAnyOtherArgumentsSet:
            if isTime and not isDistance:
                print(f"Sleep amount in critical section is {MutualExclusionAgrawalaComponent.privilegeSleepAmount} seconds.")
            elif isDistance and not isTime:
                print(f"Label drawing distance from the node is {labelDistance}.")
            else:
                helpCommand(COMMAND.GET)
        else:
            helpCommand(COMMAND.GET)
    elif isAll and not (isTime or isDistance) and not (isMean or isTotal):
        if not areAnyOtherArgumentsSet:
            isRequest = isReply = isPrivilege = isForwarded = True

        if len(args) == 0:
            for nodeID in topology.nodes:
                node = topology.nodes[nodeID]
                print(getNodeInformation(node, isRequest, isReply, isPrivilege, isForwarded))
        else:
            helpCommand(COMMAND.GET)
    elif (isMean or isTotal) and not (isTime or isDistance) and not isAll:
        if not areAnyOtherArgumentsSet:
            isRequest = isReply = isPrivilege = isForwarded = True

        if len(args) == 0:
            N = len(topology.nodes)
            node = MutualExclusionAgrawalaComponent("node", -1)

            for nodeID in topology.nodes:
                node.privilegeCount += topology.nodes[nodeID].privilegeCount
                node.sentRequestCount += topology.nodes[nodeID].sentRequestCount
                node.sentReplyCount += topology.nodes[nodeID].sentReplyCount
                node.receivedRequestCount += topology.nodes[nodeID].receivedRequestCount
                node.receivedReplyCount += topology.nodes[nodeID].receivedReplyCount
                node.forwardedMessageCount += topology.nodes[nodeID].forwardedMessageCount
            totalMessageCount = node.receivedRequestCount + node.receivedReplyCount + node.forwardedMessageCount

            if isTotal:
                node.componentinstancenumber = f"Total of {N} Nodes"
                print(getNodeInformation(node, isRequest, isReply, isPrivilege, isForwarded), f"=> Total Message Count: {totalMessageCount}")
            if isMean:
                node.componentinstancenumber = f"Mean of {N} Nodes"
                node.privilegeCount /= N
                node.sentRequestCount /= N
                node.sentReplyCount /= N
                node.receivedRequestCount /= N
                node.receivedReplyCount /= N
                node.forwardedMessageCount /= N
                print(getNodeInformation(node, isRequest, isReply, isPrivilege, isForwarded))
        else:
            helpCommand(COMMAND.GET)
    else:
        if areAnyOtherArgumentsSet and not (isTime or isDistance) and not isAll and not isMean:
            if len(args) == 1:
                try:
                    nodeID = int(args[0])
                    node = topology.nodes[nodeID]
                    print(getNodeInformation(node, isRequest, isReply, isPrivilege, isForwarded))
                except KeyError:
                    print(f"Node {nodeID} does not exist in the topology.")
                except ValueError:
                    print(f"\'{args[0]}\' is not integer.")
            else:
                helpCommand(COMMAND.GET)
        else:
            helpCommand(COMMAND.GET)

def drawGraph(overwrite=False):
    global drawnGraphNodeColors, drawnGraphNodeLabels, labelDistance, SAVED_FILE_INDEX, SAVING_ENABLED

    G = topology.G
    mstG = nx.minimum_spanning_tree(topology.G)
    pos = nx.drawing.nx_pydot.graphviz_layout(mstG, prog="neato", root=mstG.nodes[0])  # neato twopi sfdp

    nodeColors = []
    nodeLabels = []
    for nodeID in topology.nodes:
        node = topology.nodes[nodeID]
        G.nodes[nodeID]['label'] = node.clock
        nodeLabels.append(node.clock)

        if node.isPrivileged:
            nodeColors.append(PRIVILEGED_NODE_COLOR)
        elif node.havePendingRequest:
            nodeColors.append(WAITING_NODE_COLOR)
        else:
            nodeColors.append(NODE_COLOR)

    if overwrite or nodeColors != drawnGraphNodeColors or nodeLabels != drawnGraphNodeLabels:
        drawnGraphNodeColors = list(nodeColors)
        drawnGraphNodeLabels = list(nodeLabels)

        labels = nx.get_node_attributes(G, 'label')
        labelPos = {}
        centerX, centerY = pos[0]
        sumX, sumY = 0, 0
        for key in pos:
            if key == 0:
                pass
            x, y = pos[key]
            sumX, sumY = sumX + x, sumY + y
            theta = atan2(centerY - y, centerX - x)
            labelPos[key] = (x + labelDistance * cos(theta), y + labelDistance * sin(theta))
        meanX, meanY = sumX / len(pos), sumY / len(pos)
        theta = atan2(meanY - centerY, meanX - centerX)
        labelPos[0] = (centerX + labelDistance * cos(theta), centerY + labelDistance * sin(theta))

        nx.draw(G, pos, node_color=nodeColors, edge_color=EDGE_COLOR, with_labels=True, font_weight='bold')
        nx.draw_networkx_labels(G, labelPos, labels)

        plt.draw()
        if SAVING_ENABLED:
            path = os.path.join(SAVE_PATH, f"ra_{SAVED_FILE_INDEX}.png")
            plt.savefig(path, format="PNG")
            SAVED_FILE_INDEX += 1
        plt.show()



def getUserInput():
    while True:
        userInput = input("User Command: \n")
        processUserCommand(userInput)

def connectedBinomialGraph(n, p, seed=None):
    if seed is not None:
        random.seed(seed)

    if p <= 0:
        G = nx.empty_graph(n)
    elif p >= 1:
        G = nx.complete_graph(n)
    else:
        allEdges = list(combinations(range(n), 2))
        G = nx.empty_graph(n)

        for node, nodeEdges in groupby(allEdges, key=lambda x: x[0]):
            nodeEdges = list(nodeEdges)
            randomEdge = random.choice(nodeEdges)
            G.add_edge(*randomEdge)
            for edge in nodeEdges:
                if random.random() < p:
                    G.add_edge(*edge)

    if seed is not None:
        random.seed()

    return G
topology = Topology()
def main():
    global labelDistance

    G = connectedBinomialGraph(5, 0.2, seed=5)
    labelDistance = len(G.nodes)

    
    topology.construct_from_graph(G, MutualExclusionAgrawalaComponent, GenericChannel)
    topology.start()

    if os.path.exists(SAVE_PATH):
        shutil.rmtree(SAVE_PATH)
    os.makedirs(SAVE_PATH)

    userinputDaemon = threading.Thread(target=getUserInput(), daemon=True)
    userinputDaemon.start()

    while True:
        drawGraph()
        sleep(1.0/FPS)


if __name__ == "__main__":
    main()
