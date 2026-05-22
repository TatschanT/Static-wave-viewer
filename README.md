![Standing Wave Viewer image](images/SWVtitle.jpg)

Standing Wave Viewer is an 3D acoustic simulation and visualization tool built with Python and Streamlit. It calculates and visualizes room modes (standing waves) and low-frequency interference patterns to help optimize subwoofer/speaker placement and listening positions. To learn technical details behind, please refer docunets/Q_A_en.md.

Please note that this is an amateur project that began as a personal endeavor, and is not intended to serve as a fully rigorous verification tool for professional use.
I originally created it for myself, with the goal of making it as intuitive as possible to understand the acoustic characteristics of a room. However, now that it’s finished, I feel it has turned into something fairly unique, so I decided to make it available to the public.
If it proves useful to anyone out there, I couldn’t be happier.

## ✨ Key Features

- **Interactive 3D Room Setup**: Easily adjust room dimensions, speaker coordinates, and microphone positions using a sidebar UI with real-time 3D wireframe rendering.
- **Accurate Frequency Response**: Simulates the frequency response (20Hz - 200Hz) at the microphone position, accounting for room dimensions and wall reflection coefficients.
- **Volumetric 3D Visualization**: Animates the sound pressure distribution (nodes and antinodes) across the entire 3D room space for any given frequency.
- **Advanced Stereo Interference Models**: 
  Supports both Mono and Stereo configurations with three calculation modes:
  - **Uncorrelated (Independent Power Sum)**: Adds acoustic power without wave interference.
  - **In-Phase (Global Cancel - Fast)**: A fast approximation model for phase cancellation.
  - **In-Phase (True Complex Field - Experimental)**: The ultimate physics engine. It synthesizes the exact complex field (real + imaginary parts) across the entire 3D space, perfectly reproducing the spatial warping of wave nodes when subwoofers are placed asymmetrically. Please note that this mode is experimental, and its practicality cannot be guaranteed.
- **Customizable Wall Reflections**: Fine-tune the reflection coefficient (0.0 to 1.0) for all six boundaries (walls, floor, ceiling).
- **Spatial Smoothing**: This feature smooths the signal within a 3x3x3 range around the microphone's coordinates to better match how sound is actually perceived. It evens out sharp dips in the In-Phase model.
- **Optimized for Laptop Performance**: By default, it runs smoothly even on less powerful machines. You can toggle to High Resolution Mode and Large 3D View Mode for a richer desktop experience.

## 🚀 Operation Modes

1. **🎛️ Layout Placement (Ultra-fast)**: Quickly drag and drop (via sliders) speakers and mics. Provides instantaneous 1D frequency response graphs.
2. **🌊 Standing Wave Viz (Current Setup)**: Renders the full 3D volumetric tensor of sound pressure based on your layout, allowing you to "play" the animation across frequencies.
3. **📐 Room Bare Specs (Rigid/Corner)**: A baseline mode simulating a perfectly rigid room (Reflection = 1.0) with a corner-placed source to visualize the raw, pure acoustic properties of the room shape.

## 🛠️ Installation & Usage

### Prerequisites
- Python 3.7+
- `streamlit`
- `numpy`
- `plotly`

### Running the App (Local)
1. Clone the repository.
2. Install dependencies:
   ```bash
   pip install streamlit numpy plotly
   ```
3. Run the Streamlit app:
   ```bash
   streamlit run Standing_Wave_Viewer.py
   ```
Then, open the provided Local URL (usually `http://localhost:8501`) in your web browser.

### Running at streamlit cloud
Please access https://standing-wave-viewer.streamlit.app/
When the app had been suspended, please rebake.

Disclaimer

This software is provided "AS IS", without any warranty of any kind, express or implied, including but not limited to warranties of merchantability, fitness for a particular purpose, or non‑infringement.
In no event shall the author be liable for any claim, damages, or other liability arising from, out of, or in connection with the software or the use or other dealings in the software.
This software is provided as a reference and educational tool for personal use, and is not intended to serve as the sole rigorous basis for professional‑grade verification, design decisions, or commercial services.
This repository is also not intended as a venue for general discussions or assertions that are unrelated to the actual behavior, usability, or quality of this software.
Such topics are considered out of scope for this project, and issues or comments along those lines may not receive a response.