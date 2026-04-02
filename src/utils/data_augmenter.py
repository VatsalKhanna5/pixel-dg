import numpy as np
import skrf as rf

class SParamAugmenter:
    """
    Implements S-parameter data augmentation by reducing 4-port networks 
    down to arrays of 2-port structures via ideal open and short circuit 
    terminations uniformly across frequencies.
    """

    @staticmethod
    def reduce_4port_to_2port(network_4p: rf.Network, open_port: int, short_port: int) -> rf.Network:
        """
        Terminates the specified open_port with an ideal Open Circuit (Gamma=1),
        and the short_port with an ideal Short Circuit (Gamma=-1).
        
        Returns the simplified 2-port skrf.Network.
        """
        freq_obj = network_4p.frequency
        num_points = len(freq_obj)
        z0 = network_4p.z0[0,0] if network_4p.z0 is not None else 50.0
        
        # Instantiate 1-port Open and Short termination networks
        open_net = rf.Network(frequency=freq_obj, s=np.ones((num_points, 1, 1), dtype=complex), z0=z0)
        short_net = rf.Network(frequency=freq_obj, s=-np.ones((num_points, 1, 1), dtype=complex), z0=z0)
        
        terminations = [
            (open_port, open_net),
            (short_port, short_net)
        ]
        
        # We must sort the terminations in descending order of port index.
        # This prevents the higher port index from shifting out of place
        # when the lower indexed port is terminated and removed from the matrix.
        terminations.sort(key=lambda x: x[0], reverse=True)
        
        result_net = network_4p.copy()
        
        from skrf.network import connect
        for port_idx, term_net in terminations:
            # Terminate securely using cascading connections natively supported by scikit-rf
            result_net = connect(result_net, port_idx, term_net, 0)
            
        return result_net

    @staticmethod
    def generate_8_variants(s_matrix_4x4: np.ndarray, freqs_hz: np.ndarray) -> list[np.ndarray]:
        """
        Transforms the raw (N, 4, 4) FDTD scattering matrix into 8 dataset-ready 2-port variants.
        
        Ports map standard: 0 (Left), 1 (Right), 2 (Top), 3 (Bottom).
        """
        freq_obj = rf.Frequency.from_f(freqs_hz, unit='hz')
        net_4p = rf.Network(frequency=freq_obj, s=s_matrix_4x4, z0=50.0)
        
        variants = []
        
        # Variant 1: In/Out = Left/Right (0/1). Top (2) = Open, Bottom (3) = Short.
        v1 = SParamAugmenter.reduce_4port_to_2port(net_4p, open_port=2, short_port=3)
        variants.append(v1.s)
        
        # Variant 2: In/Out = Left/Right (0/1). Top (2) = Short, Bottom (3) = Open.
        v2 = SParamAugmenter.reduce_4port_to_2port(net_4p, open_port=3, short_port=2)
        variants.append(v2.s)
        
        # Variant 3: In/Out = Top/Bottom (2/3). Left (0) = Open, Right (1) = Short.
        v3 = SParamAugmenter.reduce_4port_to_2port(net_4p, open_port=0, short_port=1)
        variants.append(v3.s)
        
        # Variant 4: In/Out = Top/Bottom (2/3). Left (0) = Short, Right (1) = Open.
        v4 = SParamAugmenter.reduce_4port_to_2port(net_4p, open_port=1, short_port=0)
        variants.append(v4.s)
        
        # Variants 5-8: Mirrored inversions of Variants 1-4.
        # Swapping the 2 remaining ports (Port 1 <-> Port 2) equates to flipping the 2x2 submatrix
        for i in range(4):
            base_s = variants[i]
            # [:, ::-1, ::-1] natively swaps S11 with S22, and S21 with S12 dynamically for 2-port arrays.
            mirrored_s = base_s[:, ::-1, ::-1].copy()
            variants.append(mirrored_s)
            
        return variants

