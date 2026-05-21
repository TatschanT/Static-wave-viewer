import streamlit as st
import numpy as np
import plotly.graph_objects as go
from dataclasses import dataclass

# ==========================================
# Data Models
# ==========================================

@dataclass
class Position:
    """Represents a 3D spatial coordinate in meters."""
    x: float
    y: float
    z: float

@dataclass
class RoomConfig:
    """Stores room dimensions and wall reflection coefficients."""
    Lx: float
    Ly: float
    Lz: float
    Rx: float
    Ry: float
    Rz: float

@dataclass
class SimConfig:
    """Stores global simulation parameters and frequency arrays."""
    speed_of_sound: float
    freqs_1d: np.ndarray
    freqs_3d: np.ndarray

# ==========================================
# Application State & Configuration
# ==========================================

DEFAULT_STATE = {
    "Lx": 3.5, "Ly": 2.6, "Lz": 2.4,
    "spk_x": 0.5, "spk_y": 0.5, "spk_z": 0.5,
    "spk2_x": 3.0, "spk2_y": 0.5, "spk2_z": 0.5,
    "mic_x": 1.75, "mic_y": 1.3, "mic_z": 1.2,
    "R": 0.80  # Default generic reflection coefficient
}

st.set_page_config(page_title="Standing Wave Viewer V0.8.1", layout="wide")

# ==========================================
# UI Setup: Sidebar Controls
# ==========================================

st.sidebar.title("🎵 Standing Wave Viewer")
st.sidebar.markdown("Control Panel")

source_mode = st.sidebar.radio("Sound Source Setup", [
    "🔊 1 Source (Mono)",
    "🔊🔊 2 Sources (Stereo)"
])
num_sources = 1 if "1 Source" in source_mode else 2

if num_sources == 2:
    corr_mode = st.sidebar.radio("L/R Bass Signal Correlation", [
        "🔀 Uncorrelated (Independent Power Sum)",
        "🔗 In-Phase (Global Cancel - Fast)",
        "🌊 In-Phase (True Complex Field - experimental)"
    ], help="Uncorrelated: adds power. Global Cancel: Fast approximation for cancel. True Complex: Real-world spatial interference.")
else:
    corr_mode = "Mono (Approx)"

mode = st.sidebar.radio("Operation Mode", [
    "🎛️ 1. Layout Placement (Ultra-fast)",
    "🌊 2. Standing Wave Viz (Current Setup)",
    "📐 3. Room Bare Specs (Rigid/Corner)"
])

# Display resolution and view size toggles
st.sidebar.markdown("---")
high_res = st.sidebar.toggle("High Resolution Mode (Slower)", value=False, help="Enable 32x32x32 grid and 2Hz steps. Default is 24x24x24 grid and 5Hz steps.")
large_view = st.sidebar.toggle("Large 3D View", value=False, help="Increase the 3D graph height for high-resolution displays.")
chart_height = 800 if large_view else 500

st.sidebar.header("Room Dimensions (m)")
Lx = st.sidebar.slider("Width (Lx)", 1.0, 10.0, DEFAULT_STATE["Lx"], 0.02)
Ly = st.sidebar.slider("Depth (Ly)", 1.0, 10.0, DEFAULT_STATE["Ly"], 0.02)
Lz = st.sidebar.slider("Height (Lz)", 1.0, 5.0, DEFAULT_STATE["Lz"], 0.02)

st.sidebar.header("Equipment Positions (m)")

# Initialize session state for symmetric positioning
if "spk2_x_state" not in st.session_state:
    st.session_state["spk2_x_state"] = DEFAULT_STATE["spk2_x"]
if "spk2_y_state" not in st.session_state:
    st.session_state["spk2_y_state"] = DEFAULT_STATE["spk2_y"]
if "spk2_z_state" not in st.session_state:
    st.session_state["spk2_z_state"] = DEFAULT_STATE["spk2_z"]
if "is_linked" not in st.session_state:
    st.session_state["is_linked"] = True

if num_sources == 2:
    link_lr = st.sidebar.checkbox("🔗 L/R Symmetry Link", value=st.session_state["is_linked"], help="Automatically mirror Spk 2 based on Spk 1's position")
    st.session_state["is_linked"] = link_lr

    st.sidebar.markdown("**Spk 1 (L)**")

    # Constrain Spk 1 X coordinate if symmetry is linked
    max_x_spk1 = Lx / 2.0 if link_lr else Lx
    current_spk_x = st.session_state.get("s1x", DEFAULT_STATE["spk_x"])
    if current_spk_x > max_x_spk1:
        current_spk_x = max_x_spk1

    spk_x = st.sidebar.slider("X", 0.0, float(max_x_spk1), float(current_spk_x), 0.01, key="s1x")
    spk_y = st.sidebar.slider("Y", 0.0, Ly, DEFAULT_STATE["spk_y"], 0.01, key="s1y")
    spk_z = st.sidebar.slider("Z", 0.0, Lz, DEFAULT_STATE["spk_z"], 0.01, key="s1z")

    if link_lr:
        # Calculate mirrored coordinates internally without displaying UI sliders for Spk 2
        st.sidebar.info(f"👉 **Spk 2 (R)** is locked symmetrically at:\nX: {Lx - spk_x:.2f}m, Y: {spk_y:.2f}m, Z: {spk_z:.2f}m")
        spk2_x = float(Lx - spk_x)
        spk2_y = float(spk_y)
        spk2_z = float(spk_z)
        st.session_state["spk2_x_state"] = spk2_x
        st.session_state["spk2_y_state"] = spk2_y
        st.session_state["spk2_z_state"] = spk2_z
    else:
        st.sidebar.markdown("**Spk 2 (R)**")
        safe_spk2_x = min(st.session_state["spk2_x_state"], Lx)
        spk2_x = st.sidebar.slider("X", 0.0, Lx, float(safe_spk2_x), 0.01, key="s2x")
        spk2_y = st.sidebar.slider("Y", 0.0, Ly, st.session_state["spk2_y_state"], 0.01, key="s2y")
        spk2_z = st.sidebar.slider("Z", 0.0, Lz, st.session_state["spk2_z_state"], 0.01, key="s2z")
        
        st.session_state["spk2_x_state"] = spk2_x
        st.session_state["spk2_y_state"] = spk2_y
        st.session_state["spk2_z_state"] = spk2_z
else:
    spk_x = st.sidebar.slider("Speaker X", 0.0, Lx, DEFAULT_STATE["spk_x"], 0.01)
    spk_y = st.sidebar.slider("Speaker Y", 0.0, Ly, DEFAULT_STATE["spk_y"], 0.01)
    spk_z = st.sidebar.slider("Speaker Z", 0.0, Lz, DEFAULT_STATE["spk_z"], 0.01)
    spk2_x, spk2_y, spk2_z = spk_x, spk_y, spk_z

st.sidebar.markdown("---")
st.sidebar.markdown("**Microphone Position**")
mic_x = st.sidebar.slider("Mic X", 0.0, Lx, DEFAULT_STATE["mic_x"], 0.01)
mic_y = st.sidebar.slider("Mic Y", 0.0, Ly, DEFAULT_STATE["mic_y"], 0.01)
mic_z = st.sidebar.slider("Mic Z", 0.0, Lz, DEFAULT_STATE["mic_z"], 0.01)

with st.sidebar.expander("🧱 Wall Reflection Coefficients"):
    Rx1 = st.slider("Left Wall (X=0)", 0.0, 1.0, DEFAULT_STATE["R"], 0.05)
    Rx2 = st.slider("Right Wall (X=Lx)", 0.0, 1.0, DEFAULT_STATE["R"], 0.05)
    Ry1 = st.slider("Front Wall (Y=0)", 0.0, 1.0, DEFAULT_STATE["R"], 0.05)
    Ry2 = st.slider("Back Wall (Y=Ly)", 0.0, 1.0, DEFAULT_STATE["R"], 0.05)
    Rz1 = st.slider("Floor (Z=0)", 0.0, 1.0, DEFAULT_STATE["R"], 0.05)
    Rz2 = st.slider("Ceiling (Z=Lz)", 0.0, 1.0, DEFAULT_STATE["R"], 0.05)

Rx = (Rx1 + Rx2) / 2.0
Ry = (Ry1 + Ry2) / 2.0
Rz = (Rz1 + Rz2) / 2.0

# ==========================================
# Physics Constants & Object Initialization
# ==========================================

SPEED_OF_SOUND = 343.0
FREQS_1D = np.arange(20, 201, 1)

if high_res:
    FREQS_3D = np.arange(20, 201, 2)
    grid_size = 32
else:
    FREQS_3D = np.arange(20, 205, 5)
    grid_size = 24

room = RoomConfig(Lx=Lx, Ly=Ly, Lz=Lz, Rx=Rx, Ry=Ry, Rz=Rz)
spk1_pos = Position(x=spk_x, y=spk_y, z=spk_z)
spk2_pos = Position(x=spk2_x, y=spk2_y, z=spk2_z)
mic_pos = Position(x=mic_x, y=mic_y, z=mic_z)
sim_config = SimConfig(speed_of_sound=SPEED_OF_SOUND, freqs_1d=FREQS_1D, freqs_3d=FREQS_3D)

# ==========================================
# Core Physics Engine
# ==========================================

def get_max_modes(room: RoomConfig, config: SimConfig) -> tuple:
    """Calculates maximum modal indices (nx, ny, nz) based on room size and upper frequency limit."""
    return (
        int(2.0 * room.Lx * 250 / config.speed_of_sound) + 2,
        int(2.0 * room.Ly * 250 / config.speed_of_sound) + 2,
        int(2.0 * room.Lz * 250 / config.speed_of_sound) + 2
    )

def calc_shape(n: int, pos: float, L: float, R: float) -> float:
    """Calculates the 1D spatial mode shape function (amplitude scalar)."""
    if n == 0: return pos * 0.0 + 1.0
    return np.sqrt(1 + R**2 + 2 * R * np.cos(2 * n * np.pi * pos / L)) / (1 + R)

def get_psi(n: int, pos: float, L: float, R: float) -> complex:
    """Calculates the 1D complex mode shape function, accounting for phase and wall absorption."""
    if n == 0: return 1.0 + 0j
    theta = n * np.pi * pos / L
    return np.cos(theta) - 1j * ((1 - R) / (1 + R)) * np.sin(theta)

def calc_gamma(nx: int, ny: int, nz: int, room: RoomConfig) -> float:
    """Calculates the modal damping factor (gamma) based on wall reflection coefficients."""
    n_sum = nx + ny + nz
    if n_sum == 0: return 5.0
    R_eff = (nx * room.Rx + ny * room.Ry + nz * room.Rz) / n_sum
    return 3.0 + 40.0 * (1.0 - R_eff)

@st.cache_data(show_spinner=False)
def compute_f_response_1d(room: RoomConfig, spk1: Position, spk2: Position, mic: Position, num_src: int, corr_mode: str, config: SimConfig, smoothing: bool = False) -> np.ndarray:
    """
    Computes the 1D frequency response (SPL vs Frequency) at the microphone position(s).
    Supports spatial smoothing by averaging over a 3x3x3 grid around the mic.
    """
    Lx, Ly, Lz = room.Lx, room.Ly, room.Lz
    Rx, Ry, Rz = room.Rx, room.Ry, room.Rz
    sx, sy, sz = spk1.x, spk1.y, spk1.z
    sx2, sy2, sz2 = spk2.x, spk2.y, spk2.z
    SPEED_OF_SOUND = config.speed_of_sound
    FREQS_1D = config.freqs_1d

    if smoothing:
        d_val = 0.1
        offsets = [-d_val, 0, d_val]
        mic_positions = [(mic.x + dx, mic.y + dy, mic.z + dz) for dx in offsets for dy in offsets for dz in offsets]
    else:
        mic_positions = [(mic.x, mic.y, mic.z)]

    num_mics = len(mic_positions)
    mxs = np.clip([p[0] for p in mic_positions], 0, Lx)
    mys = np.clip([p[1] for p in mic_positions], 0, Ly)
    mzs = np.clip([p[2] for p in mic_positions], 0, Lz)

    max_nx, max_ny, max_nz = get_max_modes(room, config)

    if "True Complex Field" in corr_mode:
        P_complex_1_mics = np.zeros((num_mics, len(FREQS_1D)), dtype=complex)
        P_complex_2_mics = np.zeros((num_mics, len(FREQS_1D)), dtype=complex)

        for nx in range(max_nx):
            for ny in range(max_ny):
                for nz in range(max_nz):
                    if nx == 0 and ny == 0 and nz == 0: continue
                    fn = (SPEED_OF_SOUND / 2.0) * np.sqrt((nx/Lx)**2 + (ny/Ly)**2 + (nz/Lz)**2)
                    if fn > 250: continue

                    gamma = calc_gamma(nx, ny, nz, room)
                    psi1 = get_psi(nx, sx, Lx, Rx) * get_psi(ny, sy, Ly, Ry) * get_psi(nz, sz, Lz, Rz)
                    if num_src == 2:
                        psi2 = get_psi(nx, sx2, Lx, Rx) * get_psi(ny, sy2, Ly, Ry) * get_psi(nz, sz2, Lz, Rz)

                    rec_psis = np.array([get_psi(nx, m_x, Lx, Rx) * get_psi(ny, m_y, Ly, Ry) * get_psi(nz, m_z, Lz, Rz) for m_x, m_y, m_z in zip(mxs, mys, mzs)])

                    for i, f_query in enumerate(FREQS_1D):
                        res_complex = (50.0 / fn) / ((f_query - fn) + 1j * gamma)
                        P_complex_1_mics[:, i] += psi1 * rec_psis * res_complex
                        if num_src == 2:
                            P_complex_2_mics[:, i] += psi2 * rec_psis * res_complex

        tensor_1d_mics = np.abs(P_complex_1_mics + P_complex_2_mics)
        tensor_1d_avg = np.sqrt(np.mean(tensor_1d_mics ** 2, axis=0))

    else:
        tensor_1d_mics = np.zeros((num_mics, len(FREQS_1D)))

        for nx in range(max_nx):
            for ny in range(max_ny):
                for nz in range(max_nz):
                    if nx == 0 and ny == 0 and nz == 0: continue
                    fn = (SPEED_OF_SOUND / 2.0) * np.sqrt((nx/Lx)**2 + (ny/Ly)**2 + (nz/Lz)**2)
                    if fn > 250: continue

                    psi1 = get_psi(nx, sx, Lx, Rx) * get_psi(ny, sy, Ly, Ry) * get_psi(nz, sz, Lz, Rz)
                    if num_src == 2:
                        psi2 = get_psi(nx, sx2, Lx, Rx) * get_psi(ny, sy2, Ly, Ry) * get_psi(nz, sz2, Lz, Rz)
                        if "Global Cancel" in corr_mode:
                            exc = np.abs(psi1 + psi2) / 2.0
                        else:
                            exc = np.sqrt(np.abs(psi1)**2 + np.abs(psi2)**2) / 2.0
                    else:
                        exc = np.abs(psi1)

                    recs = np.array([calc_shape(nx, m_x, Lx, Rx) * calc_shape(ny, m_y, Ly, Ry) * calc_shape(nz, m_z, Lz, Rz) for m_x, m_y, m_z in zip(mxs, mys, mzs)])
                    gamma = calc_gamma(nx, ny, nz, room)

                    for i, f in enumerate(FREQS_1D):
                        res_amp = (50.0 / fn) / np.sqrt((f - fn)**2 + gamma**2)
                        tensor_1d_mics[:, i] += (exc * recs * res_amp) ** 2

        tensor_1d_mics = np.sqrt(tensor_1d_mics)
        tensor_1d_avg = np.sqrt(np.mean(tensor_1d_mics ** 2, axis=0))

    f_response_db = 20 * np.log10(np.clip(tensor_1d_avg, 1e-10, None))
    f_response_db = f_response_db - np.max(f_response_db)
    return f_response_db

@st.cache_data(show_spinner="Calculating spatial tensor...")
def compute_tensor_3d(room: RoomConfig, spk1: Position, spk2: Position, num_src: int, corr_mode: str, config: SimConfig, grid_size: int = 32) -> tuple:
    """
    Computes the 3D spatial pressure field tensor across all requested frequencies.
    Returns flattened meshgrid coordinates and the volumetric pressure magnitude tensor.
    """
    Lx, Ly, Lz = room.Lx, room.Ly, room.Lz
    Rx, Ry, Rz = room.Rx, room.Ry, room.Rz
    sx, sy, sz = spk1.x, spk1.y, spk1.z
    sx2, sy2, sz2 = spk2.x, spk2.y, spk2.z
    SPEED_OF_SOUND = config.speed_of_sound
    FREQS_3D = config.freqs_3d
    x = np.linspace(0, Lx, grid_size)
    y = np.linspace(0, Ly, grid_size)
    z = np.linspace(0, Lz, grid_size)
    X, Y, Z = np.meshgrid(x, y, z, indexing='ij')

    tensor = np.zeros((len(FREQS_3D), len(x), len(y), len(z)))
    max_nx, max_ny, max_nz = get_max_modes(room, config)

    if "True Complex Field" in corr_mode:
        for i, f_query in enumerate(FREQS_3D):
            P_complex_1 = np.zeros_like(X, dtype=np.complex128)
            P_complex_2 = np.zeros_like(X, dtype=np.complex128)

            for nx in range(max_nx):
                for ny in range(max_ny):
                    for nz in range(max_nz):
                        if nx == 0 and ny == 0 and nz == 0: continue
                        fn = (SPEED_OF_SOUND / 2.0) * np.sqrt((nx/Lx)**2 + (ny/Ly)**2 + (nz/Lz)**2)
                        if fn > 250: continue

                        gamma = calc_gamma(nx, ny, nz, room)
                        res_complex = (50.0 / fn) / ((f_query - fn) + 1j * gamma)

                        mode_complex = get_psi(nx, X, Lx, Rx) * get_psi(ny, Y, Ly, Ry) * get_psi(nz, Z, Lz, Rz)
                        psi1 = get_psi(nx, sx, Lx, Rx) * get_psi(ny, sy, Ly, Ry) * get_psi(nz, sz, Lz, Rz)

                        P_complex_1 += psi1 * mode_complex * res_complex

                        if num_src == 2:
                            psi2 = get_psi(nx, sx2, Lx, Rx) * get_psi(ny, sy2, Ly, Ry) * get_psi(nz, sz2, Lz, Rz)
                            P_complex_2 += psi2 * mode_complex * res_complex

            if num_src == 2:
                tensor[i] = np.abs(P_complex_1 + P_complex_2)
            else:
                tensor[i] = np.abs(P_complex_1)
    else:
        for nx in range(max_nx):
            for ny in range(max_ny):
                for nz in range(max_nz):
                    if nx == 0 and ny == 0 and nz == 0: continue
                    fn = (SPEED_OF_SOUND / 2.0) * np.sqrt((nx/Lx)**2 + (ny/Ly)**2 + (nz/Lz)**2)
                    if fn > 250: continue

                    psi1 = get_psi(nx, sx, Lx, Rx) * get_psi(ny, sy, Ly, Ry) * get_psi(nz, sz, Lz, Rz)
                    if num_src == 2:
                        psi2 = get_psi(nx, sx2, Lx, Rx) * get_psi(ny, sy2, Ly, Ry) * get_psi(nz, sz2, Lz, Rz)
                        if "Global Cancel" in corr_mode:
                            exc = np.abs(psi1 + psi2) / 2.0
                        else:
                            exc = np.sqrt(np.abs(psi1)**2 + np.abs(psi2)**2) / 2.0
                    else:
                        exc = np.abs(psi1)

                    mode_shape = calc_shape(nx, X, Lx, Rx) * calc_shape(ny, Y, Ly, Ry) * calc_shape(nz, Z, Lz, Rz)
                    gamma = calc_gamma(nx, ny, nz, room)

                    for i, f in enumerate(FREQS_3D):
                        res_amp = (50.0 / fn) / np.sqrt((f - fn)**2 + gamma**2)
                        tensor[i] += (exc * mode_shape * res_amp) ** 2

        tensor = np.sqrt(tensor)

    return X.flatten(), Y.flatten(), Z.flatten(), tensor

def draw_room_wireframe(Lx: float, Ly: float, Lz: float) -> go.Scatter3d:
    """Generates Plotly trace for the room boundaries (wireframe cube)."""
    x_lines = [0, Lx, Lx, 0, 0, 0, Lx, Lx, 0, 0, None, Lx, Lx, None, Lx, Lx, None, 0, 0]
    y_lines = [0, 0, Ly, Ly, 0, 0, 0, Ly, Ly, 0, None, 0, 0, None, Ly, Ly, None, Ly, Ly]
    z_lines = [0, 0, 0, 0, 0, Lz, Lz, Lz, Lz, Lz, None, 0, Lz, None, 0, Lz, None, 0, Lz]
    return go.Scatter3d(
        x=x_lines, y=y_lines, z=z_lines, 
        mode='lines', line=dict(color='gray', width=3), 
        name="Room Bounds", hoverinfo='skip'
    )

# ==========================================
# Rendering
# ==========================================

if num_sources == 2:
    spk_xs, spk_ys, spk_zs = [spk_x, spk2_x], [spk_y, spk2_y], [spk_z, spk2_z]
else:
    spk_xs, spk_ys, spk_zs = [spk_x], [spk_y], [spk_z]

if mode == "🎛️ 1. Layout Placement (Ultra-fast)":
    col_header1, col_header2 = st.columns([6, 4])
    with col_header1:
        st.info("💡 **Layout Placement Mode**: Adjust coordinates.")
    with col_header2:
        smoothing_on = st.toggle("Spatial Smoothing (3x3x3, ±10cm)", value=False, help="Averages 27 points around mic to smooth out local dips.")

    col1, col2 = st.columns([5, 5])

    trace_spk = go.Scatter3d(x=spk_xs, y=spk_ys, z=spk_zs, mode='markers', marker=dict(size=8, color='blue', symbol='square', line=dict(color='white', width=2)), name="Speaker(s)")
    trace_mic = go.Scatter3d(x=[mic_x], y=[mic_y], z=[mic_z], mode='markers', marker=dict(size=8, color='red', symbol='diamond', line=dict(color='white', width=2)), name="Mic")

    with col1:
        fig_layout = go.Figure(data=[draw_room_wireframe(room.Lx, room.Ly, room.Lz), trace_spk, trace_mic])
        fig_layout.update_layout(
            scene=dict(xaxis=dict(range=[-0.5, room.Lx+0.5]), yaxis=dict(range=[-0.5, room.Ly+0.5]), zaxis=dict(range=[-0.5, room.Lz+0.5]), aspectmode='data'),
            margin=dict(l=0, r=0, b=0, t=30), height=chart_height, title="3D Equipment Layout"
        )
        st.plotly_chart(fig_layout, width='stretch')

    with col2:
        f_response_db = compute_f_response_1d(room, spk1_pos, spk2_pos, mic_pos, num_sources, corr_mode, sim_config, smoothing=smoothing_on)
        fig_f = go.Figure(data=[go.Scatter(x=FREQS_1D, y=f_response_db, mode='lines+markers', line=dict(color='red', width=2))])
        fig_f.update_layout(
            xaxis_title="Frequency (Hz)", yaxis_title="Relative SPL (dB)",
            yaxis=dict(range=[-25, 2]),
            margin=dict(l=0, r=0, b=0, t=30), height=chart_height, title="Frequency Response (Max Peak = 0dB)"
        )
        st.plotly_chart(fig_f, width='stretch')

else:
    if mode == "📐 3. Room Bare Specs (Rigid/Corner)":
        eff_num_sources = 1
        eff_corr = "Mono"
        eff_spk1 = Position(0.0, 0.0, 0.0)
        eff_spk2 = Position(0.0, 0.0, 0.0)
        eff_room = RoomConfig(Lx, Ly, Lz, 1.0, 1.0, 1.0)
        spk_plot_x, spk_plot_y, spk_plot_z = [0.0], [0.0], [0.0]

        trace_spk = go.Scatter3d(x=spk_plot_x, y=spk_plot_y, z=spk_plot_z, mode='markers', marker=dict(size=8, color='black', symbol='square', line=dict(color='white', width=2)), name="Source (Corner)")
        trace_mic = go.Scatter3d(x=[mic_x], y=[mic_y], z=[mic_z], mode='markers', marker=dict(size=8, color='red', symbol='diamond', line=dict(color='white', width=2)), name="Mic (Current)")
    else:
        eff_num_sources = num_sources
        eff_corr = corr_mode
        eff_spk1 = spk1_pos
        eff_spk2 = spk2_pos
        eff_room = room
        trace_spk = go.Scatter3d(x=spk_xs, y=spk_ys, z=spk_zs, mode='markers', marker=dict(size=8, color='blue', symbol='square', line=dict(color='white', width=2)), name="Speaker(s)")
        trace_mic = go.Scatter3d(x=[mic_x], y=[mic_y], z=[mic_z], mode='markers', marker=dict(size=8, color='red', symbol='diamond', line=dict(color='white', width=2)), name="Mic")

    X_flat, Y_flat, Z_flat, tensor_abs = compute_tensor_3d(eff_room, eff_spk1, eff_spk2, eff_num_sources, eff_corr, sim_config, grid_size)
    global_min = np.min(tensor_abs)
    global_max = np.percentile(tensor_abs, 98)

    fig_vol = go.Figure()
    fig_vol.add_trace(draw_room_wireframe(eff_room.Lx, eff_room.Ly, eff_room.Lz))
    fig_vol.add_trace(trace_spk)
    fig_vol.add_trace(trace_mic)

    # Initialize volumetric data
    initial_val = tensor_abs[0].flatten().astype(np.float32)
    fig_vol.add_trace(go.Volume(
        x=X_flat, y=Y_flat, z=Z_flat, value=initial_val,
        isomin=np.percentile(initial_val, 60), isomax=global_max,
        opacity=0.3, opacityscale=[[-0.5, 0], [0, 0.2], [1, 1]],
        surface_count=12, colorscale='RdYlBu_r', cmin=global_min, cmax=global_max,
        caps=dict(x_show=False, y_show=False, z_show=False), name="Sound Pressure"
    ))

    # Add animation frames for sweeping through frequencies
    frames = []
    for i, f in enumerate(FREQS_3D):
        val = tensor_abs[i].flatten().astype(np.float32)
        frames.append(go.Frame(
            data=[go.Volume(
                value=val,
                isomin=np.percentile(val, 60), isomax=global_max,
                opacity=0.3, opacityscale=[[-0.5, 0], [0, 0.2], [1, 1]],
                surface_count=12, colorscale='RdYlBu_r', cmin=global_min, cmax=global_max,
                caps=dict(x_show=False, y_show=False, z_show=False)
            )],
            traces=[3],
            name=str(f)
        ))
    fig_vol.frames = frames

    fig_vol.update_layout(
        uirevision="constant",
        scene=dict(xaxis_title='X', yaxis_title='Y', zaxis_title='Z', aspectmode='data'),
        margin=dict(l=0, r=0, b=0, t=30), height=chart_height, showlegend=False,
        updatemenus=[dict(
            type="buttons",
            x=0.05, y=0,
            direction="left", 
            buttons=[
                dict(
                    label="Play",
                    method="animate",
                    args=[None, dict(frame=dict(duration=500, redraw=True), transition=dict(duration=0), fromcurrent=True)]
                ),
                dict(
                    label="Pause",
                    method="animate",
                    args=[[None], dict(frame=dict(duration=0, redraw=False), mode="immediate", transition=dict(duration=0))]
                )
            ]
        )],
        sliders=[dict(
            active=0, yanchor="top", xanchor="left", currentvalue=dict(font=dict(size=16), prefix="Frequency: ", suffix=" Hz"),
            transition=dict(duration=0), pad=dict(b=10, t=50), len=0.9, x=0.15, y=0,
            steps=[dict(args=[[str(f)], dict(frame=dict(duration=300, redraw=True), mode="immediate", transition=dict(duration=0))],
            label=str(f), method="animate") for f in FREQS_3D]
        )]
    )

    st.plotly_chart(fig_vol, width='stretch')