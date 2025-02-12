class Node:
    def __init__(self, data_index, split_feature=None, split_value=None, is_leaf=False, loss=None,
                 deep=None):
        self.loss = loss
        self.split_feature = split_feature
        self.split_value = split_value
        self.data_index = data_index
        self.is_leaf = is_leaf
        self.predict_value = None
        self.left_child = None
        self.right_child = None
        self.deep = deep

    def update_predict_value(self, targets, y):
        self.predict_value = self.loss.update_leaf_values(targets, y)


class Tree:
    def __init__(self, data, max_depth, min_samples_split, features, loss, target_name):

        self.tree_in_vector = []
        self.lookup = {}

        self.loss = loss
        self.max_depth = max_depth
        self.min_samples_split = min_samples_split
        self.features = features
        self.target_name = target_name
        self.remain_index = [True] * len(data)
        self.leaf_nodes = []
        self.root_node = self.build_tree(data, self.remain_index, depth=0)

    def build_tree(self, data, remain_index, depth=0):
        """
        此处有三个树继续生长的条件：
            1、深度没有到达最大 depth < self.max_depth - 1
            2、节点样本数 >= min_samples_split
            3、节点样本的target_name值不一样（如果值一样说明已经划分得很好了，不需要再分）
        """
        now_data = data[remain_index]

        if depth < self.max_depth - 1 \
                and len(now_data) >= self.min_samples_split \
                and len(now_data[self.target_name].unique()) > 1:
            se = None
            split_feature = None
            split_value = None
            left_index_of_now_data = None
            right_index_of_now_data = None
            # 划分特征
            for feature in self.features:
                # 划分值
                feature_values = now_data[feature].unique()
                for fea_val in feature_values:
                    # 尝试划分
                    left_index = list(now_data[feature] < fea_val)
                    right_index = list(now_data[feature] >= fea_val)
                    left_se = calculate_se(now_data[left_index][self.target_name])
                    right_se = calculate_se(now_data[right_index][self.target_name])
                    sum_se = left_se + right_se
                    if se is None or sum_se < se:
                        split_feature = feature
                        split_value = fea_val
                        se = sum_se
                        left_index_of_now_data = left_index
                        right_index_of_now_data = right_index

            node = Node(remain_index, split_feature, split_value, deep=depth)

            # 记录划分后样本在原始数据中的的索引
            left_index_of_all_data = []
            for i in remain_index:
                if i:
                    if left_index_of_now_data[0]:
                        left_index_of_all_data.append(True)
                        del left_index_of_now_data[0]
                    else:
                        left_index_of_all_data.append(False)
                        del left_index_of_now_data[0]
                else:
                    left_index_of_all_data.append(False)

            right_index_of_all_data = []
            for i in remain_index:
                if i:
                    if right_index_of_now_data[0]:
                        right_index_of_all_data.append(True)
                        del right_index_of_now_data[0]
                    else:
                        right_index_of_all_data.append(False)
                        del right_index_of_now_data[0]
                else:
                    right_index_of_all_data.append(False)
            
            node.left_child = self.build_tree(data, left_index_of_all_data, depth+1)
            node.right_child = self.build_tree(data, right_index_of_all_data, depth+1)

            left_node = node.left_child
            right_node = node.right_child     
            left_node_id = self.lookup[left_node]
            right_node_id = self.lookup[right_node]

            self.lookup[node] = len(self.lookup)
            self.tree_in_vector.extend([self.lookup[node],                       # node_id
                                        0,                                       # is_leaf
                                        self.features.index(node.split_feature), # split_feature
                                        split_value,                             # split_value
                                        left_node_id,                            # left_node_id
                                        right_node_id,                           # right_node_id
                                        0])                                      # predict_value - should be None

            return node
        
        else:
            node = Node(remain_index, is_leaf=True, loss=self.loss, deep=depth)
            if len(self.target_name.split('_')) == 3:
                label_name = 'label_' + self.target_name.split('_')[1]
            else:
                label_name = 'label'
            node.update_predict_value(now_data[self.target_name], now_data[label_name])
            self.leaf_nodes.append(node)

            self.lookup[node] = len(self.lookup)
            self.tree_in_vector.extend([self.lookup[node],1,0,0,0,0,node.predict_value])

            return node


def calculate_se(label):
    mean = label.mean()
    se = 0
    for y in label:
        se += (y - mean) * (y - mean)
    return se