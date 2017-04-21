from typing import List

from graph_builder.graph.operator import Operator
from graph_builder.optimizer import util
from graph_builder.optimizer.optimize_rule import OptimizeRule
from graph_builder.util import flags


class Optimizer:
    rules: List[OptimizeRule]

    def __init__(self):
        self.rules = []

    def optimize(self, graph: Operator):

        flag_retry = True
        while flag_retry:
            flag_retry = False
            for rule in self.rules:
                graph, flag_changed = rule(graph)
                flag_retry |= flag_changed
                if flags.DEBUG:
                    print(f"[Optimizer] optimize rule={rule} changed={flag_changed}")
                    util.dump(graph)
                    print()

        return graph

    def register_rule(self, rule: OptimizeRule):
        self.rules.append(rule)
