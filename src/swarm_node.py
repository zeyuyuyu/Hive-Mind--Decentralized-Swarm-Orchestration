import numpy as np
import tensorflow as tf
from typing import List

class SwarmNode:
    def __init__(self, node_id: str, neighbors: List[str]):
        self.node_id = node_id
        self.neighbors = neighbors
        self.model = self.build_model()
        self.global_model = None

    def build_model(self):
        model = tf.keras.Sequential([
            tf.keras.layers.Dense(64, activation='relu', input_shape=(100,)),
            tf.keras.layers.Dense(32, activation='relu'),
            tf.keras.layers.Dense(10, activation='softmax')
        ])
        model.compile(optimizer='adam',
                      loss='categorical_crossentropy',
                      metrics=['accuracy'])
        return model

    def train_local_model(self, X, y):
        self.model.fit(X, y, epochs=5, batch_size=32)

    def aggregate_global_model(self):
        if self.global_model is None:
            self.global_model = self.model.get_weights()
        else:
            local_weights = self.model.get_weights()
            global_weights = self.global_model
            
            # Federated averaging
            aggregated_weights = [np.average([lw, gw], axis=0, weights=[1, len(self.neighbors)]) 
                                  for lw, gw in zip(local_weights, global_weights)]
            
            self.global_model = aggregated_weights

    def update_local_model(self):
        self.model.set_weights(self.global_model)
