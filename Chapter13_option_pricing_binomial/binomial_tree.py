import math
class Node:
    def __init__(self, price,  probability=1, time = 0, option_price = None, parent=None):
        self.price = price
        self.probability = probability
        self.time = time
        self.option_price = option_price
        self.up = None  # Link to the node in the next step (up move)
        self.down = None  # Link to the node in the next step (down move)
        self.parent= parent

class BinomialTree:
    def __init__(self, initial_price, interest_rate, total_time, 
                 steps, up_factor=None, down_factor=None, strike_price= None, divident_rate=0, 
                 volatality=None, option_type = 'call', option_maturity_type='European', debug=False):
        """
        Arguments:
        initial_price: in any currency say $.
        interest_rate: continuous interest rate in percent
        total_time   : total time considered (T) in year
        up_factor    : u, the upward movement from current stock price S0 to uS0
        down_factor  : d, the downward movement from current stock price S0 to dS0
        steps        : the steps considered
        divident_rate: divident from the stock in percent
        volatality   : volatality in percent
        """

        self.time_step = total_time/steps
        self.expriry_time = total_time
        if volatality:
            up_factor = math.exp(volatality / 100 * math.sqrt(self.time_step))
            down_factor = math.exp(-volatality / 100 * math.sqrt(self.time_step))
        self.effective_interest_rate = (interest_rate-divident_rate)/(100)
        self.initial_price = initial_price
        self.up_factor = up_factor
        self.down_factor = down_factor
        self.discount_factor = math.exp(self.effective_interest_rate * self.time_step)
        self.probability_up = (self.discount_factor- down_factor) / (up_factor-down_factor)
        self.steps = steps
        self.strike_price= strike_price
        self.option_type =  option_type
        self.option_maturity_type = option_maturity_type
        self.debug = debug
        if self.debug:
            print(f'Probability = {self.probability_up}, discount factor = {self.discount_factor}, up_factor={self.up_factor}')
        self.root = Node(initial_price)

    def calculate_option_value(self, price):
        """
        Calculate the payoff at a given node based on the option type.
        
        Parameters:
        price (float): The price of the underlying asset at the node.
        
        Returns:
        float: The payoff of the option at the node.
        """
        if self.option_type == 'call':
            return max(price - self.strike_price, 0)
        elif self.option_type == 'put':
            return max(self.strike_price - price, 0)  
        else:
            raise  Error("Unsupported option type ('call' or 'put')/ option_maturity_type ('European' or 'American')")


    def build_tree(self):
        current_level = [self.root]
        for _ in range(self.steps):
            next_level = []
            for node in current_level:
                node.up = Node(node.price * self.up_factor, node.probability * self.probability_up, self.time_step + node.time, parent=node)
                node.down = Node(node.price * self.down_factor, node.probability * (1 - self.probability_up), self.time_step + node.time, parent=node)
                next_level.extend([node.up, node.down])
            current_level = next_level


        # Step 2: Calculate terminal values (at maturity)
        for node in current_level:
            node.option_price = self.calculate_option_value(node.price)  # Terminal option value at maturity

        # Step 3: Backpropagate option values
        while current_level:
            previous_level = []
            for node in current_level:
                if node.parent:  # Backpropagate to parent if it exists
                    parent = node.parent
                    option_price = (
                       (1/self.discount_factor ) *
                        (self.probability_up * parent.up.option_price + (1 - self.probability_up) * parent.down.option_price)
                    )
                    if (self.option_maturity_type == "American" and self.option_type == 'put') :
                        parent.option_price = max(option_price,  self.calculate_option_value(parent.price))
                    else: 
                        parent.option_price = option_price
                    self.calculate_option_value(node.price)
                    #print(1/self.discount_factor, self.probability_up, parent.up.option_price,parent.down.option_price )
                    if parent not in previous_level:
                        previous_level.append(parent)
            current_level = previous_level  # Move one level up for the next iteration


    def get_tree_levels(self):
        levels = []
        current_level = [self.root]
        while current_level:
            #levels.append([node.price for node in current_level])
            levels.append([[node.price, node.time, node.option_price] for node in current_level])
            next_level = []
            for node in current_level:
                if node.up: next_level.append(node.up)
                if node.down: next_level.append(node.down)
            current_level = next_level
        return levels

import matplotlib.pyplot as plt # type: ignore
import networkx as nx

def visualize_binomial_tree(tree):
    levels = tree.get_tree_levels()
    print(levels[0])
    #print(levels)
    G = nx.Graph()
    
    pos = {}
    for i, level in enumerate(levels):
        for j, property in enumerate(reversed(level)):
            price=property[0]
            time=property[1]
            option_price = property[2]
            node_id = f"{i}-{j}"
            G.add_node(node_id, price=price, time=time, option_price=option_price)
            pos[node_id] = (i, - (2**(i-1)+ 1)/ 2  +j)
            if i > 0:
                parent_id = f"{i-1}-{j//2}"
                G.add_edge(parent_id, node_id)
    labels = {node: f'S={data["price"]:.2f}$ \n t = {data["time"]:.4f}y \n f ={data["option_price"]:.4f}$' for node, data in G.nodes(data=True)}
    nx.draw(G, pos, labels=labels, with_labels=True, node_size=5000, node_color='skyblue', font_size=10, node_shape='s')
    plt.show()