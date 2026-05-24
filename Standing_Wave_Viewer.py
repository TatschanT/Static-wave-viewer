import streamlit as st
import numpy as np
import plotly.graph_objects as go
from dataclasses import dataclass
import config as app_config

# ==========================================
# Data Models
# ==========================================

@dataclass
class Position:
    x: float
    y: float
    z: float

@dataclass
class RoomConfig:
    Lx: float
    Ly: float
    Lz: float
    Rx: float
    Ry: float
    Rz: float

@dataclass
class SimConfig:
    speed_of_sound: float
    freqs_1d: np.ndarray
    freqs_3d: np.ndarray

# ==========================================
# Application State & Configuration
# ==========================================

DEFAULT_STATE = {
    "Lx": app_config.AppDefaults.LX, "Ly": app_config.AppDefaults.LY, "Lz": app_config.AppDefaults.LZ,
    "spk_x": app_config.AppDefaults.SPK_X, "spk_y": app_config.AppDefaults.SPK_Y, "spk_z": app_config.AppDefaults.SPK_Z,
    "spk2_x": app_config.AppDefaults.SPK2_X, "spk2_y": app_config.AppDefaults.SPK2_Y, "spk2_z": app_config.AppDefaults.SPK2_Z,
    "mic_x": app_config.AppDefaults.MIC_X, "mic_y": app_config.AppDefaults.MIC_Y, "mic_z": app_config.AppDefaults.MIC_Z,
    "R": app_config.AppDefaults.R
}

st.set_page_config(page_title="Standing Wave Viewer V0.9.0", layout="wide")

# ==========================================
# UI Setup: Sidebar Controls
# ==========================================

st.sidebar.image("images/SWVlogo.jpg", width='stretch')
st.sidebar.markdown("### Control Panel")

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

# UI scaling and resolution toggles
st.sidebar.markdown("---")
high_res = st.sidebar.toggle("High Resolution Mode (Slower)", value=False, help="Enable 32x32x32 grid and 2Hz steps. Default is 24x24x24 grid and 5Hz steps.")
large_view = st.sidebar.toggle("Large 3D View", value=False, help="Increase the 3D graph height for high-resolution displays.")
chart_height = app_config.AppDefaults.CHART_HEIGHT_LARGE if large_view else app_config.AppDefaults.CHART_HEIGHT_NORMAL

st.sidebar.header("Room Dimensions (m)")
Lx = st.sidebar.slider("Width (Lx)", app_config.AppDefaults.ROOM_MIN_L, app_config.AppDefaults.ROOM_MAX_L_XY, DEFAULT_STATE["Lx"], 0.02)
Ly = st.sidebar.slider("Depth (Ly)", app_config.AppDefaults.ROOM_MIN_L, app_config.AppDefaults.ROOM_MAX_L_XY, DEFAULT_STATE["Ly"], 0.02)
Lz = st.sidebar.slider("Height (Lz)", app_config.AppDefaults.ROOM_MIN_L, app_config.AppDefaults.ROOM_MAX_L_Z, DEFAULT_STATE["Lz"], 0.02)

st.sidebar.header("Equipment Positions (m)")

# Init session states for mirrored speaker layout
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

    # Enforce symmetry constraint on Spk 1 X-axis
    max_x_spk1 = Lx / 2.0 if link_lr else Lx
    current_spk_x = st.session_state.get("s1x", DEFAULT_STATE["spk_x"])
    if current_spk_x > max_x_spk1:
        current_spk_x = max_x_spk1

    spk_x = st.sidebar.slider("X", 0.0, float(max_x_spk1), float(current_spk_x), 0.01, key="s1x")
    spk_y = st.sidebar.slider("Y", 0.0, Ly, DEFAULT_STATE["spk_y"], 0.01, key="s1y")
    spk_z = st.sidebar.slider("Z", 0.0, Lz, DEFAULT_STATE["spk_z"], 0.01, key="s1z")

    if link_lr:
        # Compute mirrored Spk 2 coordinates implicitly
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

SPEED_OF_SOUND = app_config.PhysicalConfig.SPEED_OF_SOUND
FREQS_1D = np.arange(app_config.SimResolution.FREQ_1D_START, app_config.SimResolution.FREQ_1D_END, app_config.SimResolution.FREQ_1D_STEP)

if high_res:
    FREQS_3D = np.arange(app_config.SimResolution.FREQ_3D_START_HIGH, app_config.SimResolution.FREQ_3D_END_HIGH, app_config.SimResolution.FREQ_3D_STEP_HIGH)
    grid_size = app_config.SimResolution.GRID_SIZE_HIGH
else:
    FREQS_3D = np.arange(app_config.SimResolution.FREQ_3D_START_NORMAL, app_config.SimResolution.FREQ_3D_END_NORMAL, app_config.SimResolution.FREQ_3D_STEP_NORMAL)
    grid_size = app_config.SimResolution.GRID_SIZE_NORMAL

room = RoomConfig(Lx=Lx, Ly=Ly, Lz=Lz, Rx=Rx, Ry=Ry, Rz=Rz)
spk1_pos = Position(x=spk_x, y=spk_y, z=spk_z)
spk2_pos = Position(x=spk2_x, y=spk2_y, z=spk2_z)
mic_pos = Position(x=mic_x, y=mic_y, z=mic_z)
sim_config = SimConfig(speed_of_sound=SPEED_OF_SOUND, freqs_1d=FREQS_1D, freqs_3d=FREQS_3D)

# ==========================================
# Core Physics Engine
# ==========================================

def get_max_modes(room: RoomConfig, config: SimConfig) -> tuple:
    return (
        int(2.0 * room.Lx * app_config.PhysicalConfig.MAX_CALC_FREQ / app_config.PhysicalConfig.SPEED_OF_SOUND) + 2,
        int(2.0 * room.Ly * app_config.PhysicalConfig.MAX_CALC_FREQ / app_config.PhysicalConfig.SPEED_OF_SOUND) + 2,
        int(2.0 * room.Lz * app_config.PhysicalConfig.MAX_CALC_FREQ / app_config.PhysicalConfig.SPEED_OF_SOUND) + 2
    )

def calc_shape(n: int, pos: float, L: float, R: float) -> float:
    if n == 0: return pos * 0.0 + 1.0
    return np.sqrt(1 + R**2 + 2 * R * np.cos(2 * n * np.pi * pos / L)) / (1 + R)

def get_psi(n: int, pos: float, L: float, R: float) -> complex:
    if n == 0: return 1.0 + 0j
    theta = n * np.pi * pos / L
    return np.cos(theta) - 1j * ((1 - R) / (1 + R)) * np.sin(theta)

def calc_gamma(nx: int, ny: int, nz: int, room: RoomConfig) -> float:
    n_sum = nx + ny + nz
    if n_sum == 0: return app_config.PhysicalConfig.GAMMA_ZERO_SUM
    R_eff = (nx * room.Rx + ny * room.Ry + nz * room.Rz) / n_sum
    return app_config.PhysicalConfig.GAMMA_BASE + app_config.PhysicalConfig.GAMMA_SCALE * (1.0 - R_eff)

@st.cache_data(show_spinner=False)
def compute_f_response_1d(room: RoomConfig, spk1: Position, spk2: Position, mic: Position, num_src: int, corr_mode: str, config: SimConfig, smoothing: bool = False) -> np.ndarray:
    Lx, Ly, Lz = room.Lx, room.Ly, room.Lz
    Rx, Ry, Rz = room.Rx, room.Ry, room.Rz
    sx, sy, sz = spk1.x, spk1.y, spk1.z
    sx2, sy2, sz2 = spk2.x, spk2.y, spk2.z

    if smoothing:
        d_val = app_config.SimResolution.SMOOTHING_OFFSET
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
                    if fn > app_config.PhysicalConfig.MAX_CALC_FREQ: continue

                    gamma = calc_gamma(nx, ny, nz, room)
                    psi1 = get_psi(nx, sx, Lx, Rx) * get_psi(ny, sy, Ly, Ry) * get_psi(nz, sz, Lz, Rz)
                    if num_src == 2:
                        psi2 = get_psi(nx, sx2, Lx, Rx) * get_psi(ny, sy2, Ly, Ry) * get_psi(nz, sz2, Lz, Rz)

                    rec_psis = np.array([get_psi(nx, m_x, Lx, Rx) * get_psi(ny, m_y, Ly, Ry) * get_psi(nz, m_z, Lz, Rz) for m_x, m_y, m_z in zip(mxs, mys, mzs)])

                    for i, f_query in enumerate(FREQS_1D):
                        res_complex = (app_config.PhysicalConfig.RESONANCE_SCALING / fn) / ((f_query - fn) + 1j * gamma)
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
                    if fn > app_config.PhysicalConfig.MAX_CALC_FREQ: continue

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
                        res_amp = (app_config.PhysicalConfig.RESONANCE_SCALING / fn) / np.sqrt((f - fn)**2 + gamma**2)
                        tensor_1d_mics[:, i] += (exc * recs * res_amp) ** 2

        tensor_1d_mics = np.sqrt(tensor_1d_mics)
        tensor_1d_avg = np.sqrt(np.mean(tensor_1d_mics ** 2, axis=0))

    f_response_db = 20 * np.log10(np.clip(tensor_1d_avg, app_config.PhysicalConfig.DB_CLIP_MIN, None))
    f_response_db = f_response_db - np.max(f_response_db)
    return f_response_db

@st.cache_data(show_spinner="Calculating spatial tensor...")
def compute_tensor_3d(room: RoomConfig, spk1: Position, spk2: Position, num_src: int, corr_mode: str, config: SimConfig, grid_size: int = 32) -> tuple:
    Lx, Ly, Lz = room.Lx, room.Ly, room.Lz
    Rx, Ry, Rz = room.Rx, room.Ry, room.Rz
    sx, sy, sz = spk1.x, spk1.y, spk1.z
    sx2, sy2, sz2 = spk2.x, spk2.y, spk2.z
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
                        if fn > app_config.PhysicalConfig.MAX_CALC_FREQ: continue

                        gamma = calc_gamma(nx, ny, nz, room)
                        res_complex = (app_config.PhysicalConfig.RESONANCE_SCALING / fn) / ((f_query - fn) + 1j * gamma)

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
                    if fn > app_config.PhysicalConfig.MAX_CALC_FREQ: continue

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
                        res_amp = (app_config.PhysicalConfig.RESONANCE_SCALING / fn) / np.sqrt((f - fn)**2 + gamma**2)
                        tensor[i] += (exc * mode_shape * res_amp) ** 2

        tensor = np.sqrt(tensor)

    return X.flatten(), Y.flatten(), Z.flatten(), tensor

def draw_room_wireframe(Lx: float, Ly: float, Lz: float) -> list[go.Scatter3d]:
    # 1. Room Boundaries
    x_lines = [0, Lx, Lx, 0, 0, 0, Lx, Lx, 0, 0, None, Lx, Lx, None, Lx, Lx, None, 0, 0]
    y_lines = [0, 0, Ly, Ly, 0, 0, 0, Ly, Ly, 0, None, 0, 0, None, Ly, Ly, None, Ly, Ly]
    z_lines = [0, 0, 0, 0, 0, Lz, Lz, Lz, Lz, Lz, None, 0, Lz, None, 0, Lz, None, 0, Lz]

    bounds_trace = go.Scatter3d(
        x=x_lines, y=y_lines, z=z_lines,
        mode='lines', line=dict(color='gray', width=3),
        name='Room Bounds', hoverinfo='skip'
    )

    # 2. 1/4 Subdivision Grid
    gx, gy, gz = [], [], []

    # X-axis divisions
    for i in [1, 2, 3]:
        x = Lx * i / 4.0
        gx.extend([x, x, None, x, x, None, x, x, None, x, x, None])
        gy.extend([0, Ly, None, 0, Ly, None, 0, 0, None, Ly, Ly, None])
        gz.extend([0, 0, None, Lz, Lz, None, 0, Lz, None, 0, Lz, None])

    # Y-axis divisions
    for i in [1, 2, 3]:
        y = Ly * i / 4.0
        gx.extend([0, Lx, None, 0, Lx, None, 0, 0, None, Lx, Lx, None])
        gy.extend([y, y, None, y, y, None, y, y, None, y, y, None])
        gz.extend([0, 0, None, Lz, Lz, None, 0, Lz, None, 0, Lz, None])

    # Z-axis divisions
    for i in [1, 2, 3]:
        z = Lz * i / 4.0
        gx.extend([0, Lx, None, 0, Lx, None, 0, 0, None, Lx, Lx, None])
        gy.extend([0, 0, None, Ly, Ly, None, 0, Ly, None, 0, Ly, None])
        gz.extend([z, z, None, z, z, None, z, z, None, z, z, None])

    grid_trace = go.Scatter3d(
        x=gx, y=gy, z=gz,
        mode='lines', line=dict(color='lightgray', width=1),
        name='1/4 Grid', hoverinfo='skip'
    )

    return [bounds_trace, grid_trace]

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
        st.info("Layout Placement Mode: Adjust coordinates with top-down 2D view.")
    with col_header2:
        smoothing_on = st.toggle("Spatial Smoothing (3x3x3, 10cm)", value=False, help="Averages 27 points around mic to smooth out local dips.")

    col1, col2 = st.columns([5, 5])

    with col1:
        fig_layout = go.Figure()

        # Room boundaries
        fig_layout.add_trace(go.Scatter(
            x=[0, room.Lx, room.Lx, 0, 0],
            y=[0, 0, room.Ly, room.Ly, 0],
            mode='lines', line=dict(color='gray', width=3),
            name='Room Bounds', hoverinfo='skip'
        ))

        # 4x4 internal grid lines
        for i in [1, 2, 3]:
            # X-axis divisions
            x_val = room.Lx * i / 4.0
            fig_layout.add_trace(go.Scatter(
                x=[x_val, x_val], y=[0, room.Ly],
                mode='lines', line=dict(color='lightgray', width=1, dash='dash'),
                showlegend=False, hoverinfo='skip'
            ))
            # Y-axis divisions
            y_val = room.Ly * i / 4.0
            fig_layout.add_trace(go.Scatter(
                x=[0, room.Lx], y=[y_val, y_val],
                mode='lines', line=dict(color='lightgray', width=1, dash='dash'),
                showlegend=False, hoverinfo='skip'
            ))

        # Plot Equipment (Speakers)
        spk_texts = [f"Spk 1<br>Z: {spk_zs[0]:.2f}m"] if num_sources == 1 else [f"Spk L<br>Z: {spk_zs[0]:.2f}m", f"Spk R<br>Z: {spk_zs[1]:.2f}m"]
        fig_layout.add_trace(go.Scatter(
            x=spk_xs, y=spk_ys, mode='markers+text',
            marker=dict(size=12, color='blue', symbol='square', line=dict(color='white', width=2)),
            text=spk_texts, textposition="top center",
            name="Speaker(s)"
        ))

        # Plot Microphone
        fig_layout.add_trace(go.Scatter(
            x=[mic_x], y=[mic_y], mode='markers+text',
            marker=dict(size=12, color='red', symbol='diamond', line=dict(color='white', width=2)),
            text=[f"Mic<br>Z: {mic_z:.2f}m"], textposition="top center",
            name="Mic"
        ))

        # Configure layout: remove margins to attach rulers directly to walls
        fig_layout.update_layout(
            xaxis=dict(
                range=[0, room.Lx], title="Width (X) [m]",
                dtick=0.5, ticks="inside", ticklen=8,
                minor=dict(dtick=0.1, ticks="inside", ticklen=4),
                showgrid=False, zeroline=False
            ),
            yaxis=dict(
                range=[0, room.Ly], title="Depth (Y) [m]",
                dtick=0.5, ticks="inside", ticklen=8,
                minor=dict(dtick=0.1, ticks="outside", ticklen=4),
                showgrid=False, zeroline=False
            ),
            yaxis_scaleanchor="x",
            yaxis_scaleratio=1,
            margin=dict(l=6, r=6, b=6, t=25),
            height=chart_height,
            title="Top-Down Placement View (XY Plane)"
        )
        # 'responsive': True forces Plotly to recalculate size on window resize
        st.plotly_chart(fig_layout, width='stretch', config={'responsive': True})

    with col2:
        f_response_db = compute_f_response_1d(room, spk1_pos, spk2_pos, mic_pos, num_sources, corr_mode, sim_config, smoothing=smoothing_on)
        fig_f = go.Figure(data=go.Scatter(x=sim_config.freqs_1d, y=f_response_db, mode='lines+markers', line=dict(color='red', width=2)))
        fig_f.update_layout(
            xaxis_title="Frequency (Hz)", yaxis_title="Relative SPL (dB)",
            yaxis=dict(range=[-25, 2]),
            margin=dict(l=10, r=10, b=10, t=30), height=chart_height, title="Frequency Response (Max Peak = 0dB)"
        )
        # Make chart responsive to resize
        st.plotly_chart(fig_f, width='stretch', config={'responsive': True})

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

    fig_vol = go.Figure()

    for trace in draw_room_wireframe(eff_room.Lx, eff_room.Ly, eff_room.Lz):
        fig_vol.add_trace(trace)

    fig_vol.add_trace(trace_spk)
    fig_vol.add_trace(trace_mic)

    # --- Statistical Scaling via Standard Deviation ---
    mean_val = np.mean(tensor_abs)
    std_val = np.std(tensor_abs)

    # Calculate ±2 sigma range (covers ~95.4% of data). Clip lower bound to 0.
    robust_min = max(0.0, mean_val - 2 * std_val)
    robust_max = mean_val + 2 * std_val

    # Define visual thresholds within the 2-sigma robust range (30% for valleys, 70% for peaks)
    range_span = robust_max - robust_min
    fixed_valley_max = robust_min + range_span * 0.3
    fixed_peak_min = robust_min + range_span * 0.7

    # Use absolute min/max for physical volume bounds to prevent visual clipping
    abs_min = np.min(tensor_abs)
    abs_max = np.max(tensor_abs)

    # --- Init Volumetric Traces ---
    initial_val = tensor_abs[0].flatten().astype(np.float32)

    # Trace 4: Valleys
    fig_vol.add_trace(go.Volume(
        x=X_flat, y=Y_flat, z=Z_flat, value=initial_val,
        isomin=abs_min,
        isomax=fixed_valley_max,
        opacity=0.25, surface_count=8, colorscale='RdYlBu_r',
        cmin=robust_min, cmax=robust_max, # Map colorscale to robust ±2 sigma range
        caps=dict(x_show=False, y_show=False, z_show=False),
        name='Valleys', showscale=False
    ))

    # Trace 5: Peaks
    fig_vol.add_trace(go.Volume(
        x=X_flat, y=Y_flat, z=Z_flat, value=initial_val,
        isomin=fixed_peak_min,
        isomax=abs_max,
        opacity=0.3, surface_count=6, colorscale='RdYlBu_r',
        cmin=robust_min, cmax=robust_max, # Same as above
        caps=dict(x_show=False, y_show=False, z_show=False),
        name='Peaks'
    ))

    # --- Generate Animation Frames ---
    frames = []
    for i, f in enumerate(sim_config.freqs_3d):
        val = tensor_abs[i].flatten().astype(np.float32)
        frames.append(go.Frame(
            data=[
                go.Volume(value=val, isomin=abs_min, isomax=fixed_valley_max),
                go.Volume(value=val, isomin=fixed_peak_min, isomax=abs_max)
            ],
            traces=[4, 5], # Important: Targets trace indices 4 (Valleys) and 5 (Peaks)
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
                        label=str(f), method="animate") for f in sim_config.freqs_3d]
        )]
    )
    st.plotly_chart(fig_vol, width='stretch')

if "3." in mode:
    import pandas as pd

    st.markdown("### Fundamental Room Modes (1st to 3rd Order)")

    # Fundamental room modes (Name, nx, ny, nz)
    base_modes = [
        ("Axial X (1,0,0)", 1, 0, 0),
        ("Axial Y (0,1,0)", 0, 1, 0),
        ("Axial Z (0,0,1)", 0, 0, 1),
        ("Tangential XY (1,1,0)", 1, 1, 0),
        ("Tangential XZ (1,0,1)", 1, 0, 1),
        ("Tangential YZ (0,1,1)", 0, 1, 1),
        ("Oblique (1,1,1)", 1, 1, 1)
    ]

    table_data = []
    c = sim_config.speed_of_sound

    for name, nx, ny, nz in base_modes:
        # Calculate 1st order frequency
        f1 = (c / 2.0) * np.sqrt((nx/room.Lx)**2 + (ny/room.Ly)**2 + (nz/room.Lz)**2)
        # Calculate equivalent path length (half-wavelength)
        length = c / (2.0 * f1)

        table_data.append({
            "Mode": name,
            "Length (m)": round(length, 2),
            "1st (Hz)": round(f1, 1),
            "2nd (Hz)": round(f1 * 2, 1),
            "3rd (Hz)": round(f1 * 3, 1)
        })

    df_modes = pd.DataFrame(table_data)

    # Render table without index column
    st.dataframe(df_modes, width='stretch', hide_index=True)

    # Setup CSV export payload
    csv_data = df_modes.to_csv(index=False).encode('utf-8-sig')
    st.download_button(
        label="📥 Download Table as CSV",
        data=csv_data,
        file_name="room_modes_specs.csv",
        mime="text/csv"
    )