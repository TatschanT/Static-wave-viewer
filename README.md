# 🎵 Standing Wave Viewer V0.1

A 4D Room Acoustics Simulator built with Python, Streamlit, and Plotly.
This tool visualizes standing waves (room modes) in a 3D space and calculates the frequency response (SPL) at a specific listener position, taking speaker placement and wall reflection coefficients into account.

## Features (3 Operation Modes)
1. **Layout Placement (Ultra-fast)**: 
   Drag sliders to move your speaker and mic. See the frequency response change in real-time to find the flattest sweet spot.
2. **Standing Wave Viz**: 
   Renders a 3D volume visualization of the acoustic energy distribution across the room based on your placement.
3. **Room Bare Specs**: 
   Shows the inherent worst-case standing waves (rigid walls, corner speaker placement) to help you understand where the natural "valleys" are.

## Installation

1. Clone this repository or download the files.
2. Install the required libraries:
   ```bash
   pip install -r requirements.txt
   ```

## How to Run

Run the following command in your terminal:
```bash
streamlit run Static_Wave_Viewer_V0_1.py
```
Then, open the provided Local URL (usually `http://localhost:8501`) in your web browser.
