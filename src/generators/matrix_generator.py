import numpy as np
from typing import Iterator, Tuple

class PixelLayoutGenerator:
    """
    Generates 15x15 binary matrices representing pixelated layouts
    with configurable distributions and connectivity validation.
    """

    def __init__(self):
        """Initializes internal configuration constants for 15x15 grids."""
        self.grid_size = 15
        self.dist_mean = 0.50
        self.dist_std = 0.15
        self.port_locations = [(0, 7), (14, 7), (7, 0), (7, 14)]

    def generate_raw_matrix(self) -> np.ndarray:
        """
        Generate a 15x15 matrix using a normal distribution (mu=0.5, sigma=0.15).
        Clips to [0, 1] and applies a 0.5 threshold to make it binary.
        """
        raw = np.random.normal(loc=self.dist_mean, scale=self.dist_std, size=(self.grid_size, self.grid_size))
        clipped = np.clip(raw, 0.0, 1.0)
        binary_matrix = (clipped >= 0.5).astype(int)
        return binary_matrix

    def check_dfs_connectivity(self, matrix: np.ndarray) -> bool:
        """
        Implement a Depth-First Search to verify connectivity.
        The 4 ports connect at the centers of the edges: (0, 7), (14, 7), (7, 0), (7, 14).
        
        Returns:
            bool: True if a continuous path of 1s connects at least two 
                  of these exact port locations.
        """
        # Ensure targeted ports actually rest on conductor elements (1) internally before DFS mapping
        active_ports = [p for p in self.port_locations if matrix[p] == 1]
        
        if len(active_ports) < 2:
            return False

        visited = set()
        
        def dfs(start_node: Tuple[int, int]) -> set:
            stack = [start_node]
            component = set()
            while stack:
                r, c = stack.pop()
                if (r, c) not in visited:
                    visited.add((r, c))
                    component.add((r, c))
                    # Assess non-diagonal neighbor pixels
                    for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                        nr, nc = r + dr, c + dc
                        if 0 <= nr < self.grid_size and 0 <= nc < self.grid_size:
                            if matrix[nr, nc] == 1 and (nr, nc) not in visited:
                                stack.append((nr, nc))
            return component

        for start_port in active_ports:
            if start_port not in visited:
                connected_component = dfs(start_port)
                # Confirm we reach more than 1 port to constitute a connected two-port link geometry
                ports_in_component = sum(1 for p in active_ports if p in connected_component)
                if ports_in_component >= 2:
                    return True
                    
        return False

    def generate_dataset(self, total_samples: int) -> Iterator[Tuple[np.ndarray, bool]]:
        """
        Loop and yield matrices until obtaining the exact distribution
        ratio of connected (80%) vs disconnected (20%) matrices automatically.
        """
        target_connected = int(total_samples * 0.80)
        target_disconnected = total_samples - target_connected
        
        connected_count = 0
        disconnected_count = 0
        
        while connected_count < target_connected or disconnected_count < target_disconnected:
            mat = self.generate_raw_matrix()
            is_connected = self.check_dfs_connectivity(mat)
            
            if is_connected and connected_count < target_connected:
                connected_count += 1
                yield mat, True
            elif not is_connected and disconnected_count < target_disconnected:
                disconnected_count += 1
                yield mat, False
