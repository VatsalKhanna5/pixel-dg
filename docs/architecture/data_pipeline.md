# Machine Learning Data Pipeline

The ultimate deliverable of this pipeline is to orchestrate datasets formatted exclusively for deep learning architectures (CNNs/GNNs). Simulating complex spatial geometries is an exceptionally high-latency task. To artificially increase dataset cardinality mathematically efficiently, the orchestration architecture implements physical network mirroring transformations.

## 1. 4-Port Matrix Extraction

The underlying `openEMS` mesh simulates the active trace structure once as a 4-port symmetric network. The returned complex array exists initially as:
`[Freqs, Port_RX, Port_TX]`

## 2. Ideal Network Impedance Terminations

To train a straightforward $2 \times 2$ convolutional system, the unneeded ports must be correctly collapsed mathematically using scattering reduction theory. Natively orchestrated over the Python package `scikit-rf` (`skrf`), we apply terminal loads at specific vectors.

To simulate standard 2-port network flow, extraneous bias nodes are mapped dynamically: 
* One port is loaded with an **Ideal Open Circuit**: Reflection Coefficient $\Gamma = 1$.
* The opposing perpendicular port is loaded with an **Ideal Short Circuit**: Reflection Coefficient $\Gamma = -1$.

Using recursive `skrf.connect()`, the multi-port system accurately aggregates the terminal loads without needing to re-run the FDTD simulation geometrically.

## 3. Data Augmentation (8 Variants)

A single processed 4x4 simulation dynamically spins up 8 independent $2 \times 2$ matrices by manipulating port symmetry parameters.

* **Variant 1:** Core Transmit Right ($S_{21}$). Top = Open, Bottom = Short.
* **Variant 2:** Core Transmit Right ($S_{21}$). Top = Short, Bottom = Open.
* **Variant 3:** Core Transmit Down ($S_{43}$). Left = Open, Right = Short.
* **Variant 4:** Core Transmit Down ($S_{43}$). Left = Short, Right = Open.

**Variants 5-8 (Matrix Mirroring):**
Because scattering properties inside passive networks act bidirectionally, we generate variants 5 through 8 purely by applying NumPy slice mirroring `[:, ::-1, ::-1]` on the base structures, which fundamentally flips standard transmission coordinates ($S_{11} \leftrightarrow S_{22}$ and $S_{21} \leftrightarrow S_{12}$).

## 4. HDF5 Storage Model

The final outputs are buffered into `class_f_dataset.h5` using Python's `h5py`.

The datasets are allocated dynamically with `maxshape=(None, ...)` to ensure that massive orchestration loops can scale to tens of thousands of variant topologies sequentially, continuously dumping block arrays directly from RAM to the OS physical disk layer seamlessly exactly every 10 iterations.
