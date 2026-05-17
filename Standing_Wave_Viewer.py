import streamlit as st
import numpy as np
import plotly.graph_objects as go

st.set_page_config(page_title="Standing Wave Viewer V0.2", layout="wide")
st.title("🎵 Standing Wave Viewer V0.2")

# ==========================================
# UI: Sidebar (Common Settings)
# ==========================================
st.sidebar.title("Control Panel")
mode = st.sidebar.radio("Operation Mode", [
    "🎛️ 1. Layout Placement (Ultra-fast)", 
    "🌊 2. Standing Wave Viz (Current Setup)", 
    "📐 3. Room Bare Specs (Rigid/Corner)"
])

st.sidebar.header("Room Dimensions (m)")
Lx = st.sidebar.slider("Width (Lx)", 2.0, 10.0, 3.5, 0.1)
Ly = st.sidebar.slider("Depth (Ly)", 2.0, 10.0, 2.6, 0.1)
Lz = st.sidebar.slider("Height (Lz)", 2.0, 5.0, 2.4, 0.1)

st.sidebar.header("Equipment Positions (m)")
spk_x = st.sidebar.slider("Speaker X", 0.0, Lx, 0.5, 0.01)
spk_y = st.sidebar.slider("Speaker Y", 0.0, Ly, 0.5, 0.01)
spk_z = st.sidebar.slider("Speaker Z", 0.0, Lz, 0.5, 0.01)

mic_x = st.sidebar.slider("Mic X", 0.0, Lx, Lx/2, 0.01)
mic_y = st.sidebar.slider("Mic Y", 0.0, Ly, Ly/2, 0.01)
mic_z = st.sidebar.slider("Mic Z", 0.0, Lz, Lz/2, 0.01)

with st.sidebar.expander("🧱 Wall Reflection Coefficients (0.0=Absorb ~ 1.0=Reflect)"):
    st.markdown("**X-axis (Left/Right Walls)**")
    Rx1 = st.slider("Left Wall (X=0)", 0.0, 1.0, 0.80, 0.05)
    Rx2 = st.slider("Right Wall (X=Lx)", 0.0, 1.0, 0.80, 0.05)
    st.markdown("**Y-axis (Front/Back Walls)**")
    Ry1 = st.slider("Front Wall (Y=0)", 0.0, 1.0, 0.80, 0.05)
    Ry2 = st.slider("Back Wall (Y=Ly)", 0.0, 1.0, 0.80, 0.05)
    st.markdown("**Z-axis (Floor/Ceiling)**")
    Rz1 = st.slider("Floor (Z=0)", 0.0, 1.0, 0.80, 0.05)
    Rz2 = st.slider("Ceiling (Z=Lz)", 0.0, 1.0, 0.80, 0.05)

Rx = (Rx1 + Rx2) / 2.0
Ry = (Ry1 + Ry2) / 2.0
Rz = (Rz1 + Rz2) / 2.0

# ==========================================
# Physics Calculation Engine
# ==========================================
SPEED_OF_SOUND = 343.0
FREQS_1D = np.arange(20, 201, 1)
FREQS_3D = np.arange(20, 201, 2)

def get_max_modes(Lx, Ly, Lz):
    return (
        int(2.0 * Lx * 250 / SPEED_OF_SOUND) + 2,
        int(2.0 * Ly * 250 / SPEED_OF_SOUND) + 2,
        int(2.0 * Lz * 250 / SPEED_OF_SOUND) + 2
    )

# Spatial shape of incomplete standing waves considering reflection (SWR formulation)
def calc_shape(n, pos, L, R):
    if n == 0:
        return pos * 0.0 + 1.0
    return np.sqrt(1 + R**2 + 2 * R * np.cos(2 * n * np.pi * pos / L)) / (1 + R)

# Mode attenuation rate (Dynamically calculates Q factor from reflection)
def calc_gamma(nx, ny, nz, Rx, Ry, Rz):
    n_sum = nx + ny + nz
    if n_sum == 0: return 5.0
    R_eff = (nx * Rx + ny * Ry + nz * Rz) / n_sum
    return 3.0 + 40.0 * (1.0 - R_eff)

@st.cache_data(show_spinner=False)
def compute_f_response_1d(Lx, Ly, Lz, sx, sy, sz, mx, my, mz, Rx, Ry, Rz):
    max_nx, max_ny, max_nz = get_max_modes(Lx, Ly, Lz)
    tensor_1d = np.zeros(len(FREQS_1D))
    
    for nx in range(max_nx):
        for ny in range(max_ny):
            for nz in range(max_nz):
                if nx == 0 and ny == 0 and nz == 0: continue
                fn = (SPEED_OF_SOUND / 2.0) * np.sqrt((nx/Lx)**2 + (ny/Ly)**2 + (nz/Lz)**2)
                if fn > 250: continue
                
                exc = calc_shape(nx, sx, Lx, Rx) * calc_shape(ny, sy, Ly, Ry) * calc_shape(nz, sz, Lz, Rz)
                rec = calc_shape(nx, mx, Lx, Rx) * calc_shape(ny, my, Ly, Ry) * calc_shape(nz, mz, Lz, Rz)
                gamma = calc_gamma(nx, ny, nz, Rx, Ry, Rz)
                
                for i, f in enumerate(FREQS_1D):
                    # Normalize with (50.0 / fn) to emulate flat acoustic characteristics
                    res_amp = (50.0 / fn) / np.sqrt((f - fn)**2 + gamma**2)
                    tensor_1d[i] += (exc * rec * res_amp) ** 2
                    
    f_response_db = 20 * np.log10(np.clip(np.sqrt(tensor_1d), 1e-10, None))
    # Normalize the maximum peak to 0 dB
    f_response_db = f_response_db - np.max(f_response_db)
    return f_response_db

@st.cache_data(show_spinner="Calculating spatial tensor...")
def compute_tensor_3d(Lx, Ly, Lz, sx, sy, sz, Rx, Ry, Rz):
    x = np.linspace(0, Lx, 32)
    y = np.linspace(0, Ly, 32)
    z = np.linspace(0, Lz, 32)
    X, Y, Z = np.meshgrid(x, y, z, indexing='ij')

    tensor = np.zeros((len(FREQS_3D), len(x), len(y), len(z)))
    max_nx, max_ny, max_nz = get_max_modes(Lx, Ly, Lz)

    for nx in range(max_nx):
        for ny in range(max_ny):
            for nz in range(max_nz):
                if nx == 0 and ny == 0 and nz == 0: continue
                fn = (SPEED_OF_SOUND / 2.0) * np.sqrt((nx/Lx)**2 + (ny/Ly)**2 + (nz/Lz)**2)
                if fn > 250: continue
                
                exc = calc_shape(nx, sx, Lx, Rx) * calc_shape(ny, sy, Ly, Ry) * calc_shape(nz, sz, Lz, Rz)
                mode_shape = calc_shape(nx, X, Lx, Rx) * calc_shape(ny, Y, Ly, Ry) * calc_shape(nz, Z, Lz, Rz)
                gamma = calc_gamma(nx, ny, nz, Rx, Ry, Rz)

                for i, f in enumerate(FREQS_3D):
                    # Normalize with (50.0 / fn) to emulate flat acoustic characteristics
                    res_amp = (50.0 / fn) / np.sqrt((f - fn)**2 + gamma**2)
                    tensor[i] += (exc * mode_shape * res_amp) ** 2

    return X.flatten(), Y.flatten(), Z.flatten(), np.sqrt(tensor)

def draw_room_wireframe(Lx, Ly, Lz):
    x_lines = [0, Lx, Lx, 0, 0, 0, Lx, Lx, 0, 0, None, Lx, Lx, None, Lx, Lx, None, 0, 0]
    y_lines = [0, 0, Ly, Ly, 0, 0, 0, Ly, Ly, 0, None, 0, 0, None, Ly, Ly, None, Ly, Ly]
    z_lines = [0, 0, 0, 0, 0, Lz, Lz, Lz, Lz, Lz, None, 0, Lz, None, 0, Lz, None, 0, Lz]
    return go.Scatter3d(x=x_lines, y=y_lines, z=z_lines, mode='lines', line=dict(color='gray', width=3), name="Room", hoverinfo='skip')

# ==========================================
# Rendering
# ==========================================
if mode == "🎛️ 1. Layout Placement (Ultra-fast)":
    st.info("💡 **Layout Placement Mode**: Move the equipment to find a flat frequency response. Lowering the reflection coefficient smooths out the peaks.")
    col1, col2 = st.columns([5, 5])
    
    trace_spk = go.Scatter3d(x=[spk_x], y=[spk_y], z=[spk_z], mode='markers', marker=dict(size=8, color='blue', symbol='square', line=dict(color='white', width=2)), name="Speaker")
    trace_mic = go.Scatter3d(x=[mic_x], y=[mic_y], z=[mic_z], mode='markers', marker=dict(size=8, color='red', symbol='diamond', line=dict(color='white', width=2)), name="Mic")

    with col1:
        fig_layout = go.Figure(data=[draw_room_wireframe(Lx, Ly, Lz), trace_spk, trace_mic])
        fig_layout.update_layout(
            scene=dict(xaxis=dict(range=[-0.5, Lx+0.5]), yaxis=dict(range=[-0.5, Ly+0.5]), zaxis=dict(range=[-0.5, Lz+0.5]), aspectmode='data'),
            margin=dict(l=0, r=0, b=0, t=30), height=500, title="3D Equipment Layout"
        )
        st.plotly_chart(fig_layout, width='stretch')
        
    with col2:
        f_response_db = compute_f_response_1d(Lx, Ly, Lz, spk_x, spk_y, spk_z, mic_x, mic_y, mic_z, Rx, Ry, Rz)
        fig_f = go.Figure(data=[go.Scatter(x=FREQS_1D, y=f_response_db, mode='lines+markers', line=dict(color='red', width=2))])
        fig_f.update_layout(
            xaxis_title="Frequency (Hz)", yaxis_title="Relative SPL (dB)",
            yaxis=dict(range=[-25, 2]), 
            margin=dict(l=0, r=0, b=0, t=30), height=500, title="Frequency Response (Max Peak = 0dB)"
        )
        st.plotly_chart(fig_f, width='stretch')

else:
    if mode == "📐 3. Room Bare Specs (Rigid/Corner)":
        st.info("💡 **Room Bare Characteristics Mode**: Visualizes the 'inherent worst-case standing waves' with the speaker placed in the corner (0,0,0) and perfectly rigid walls (reflection 1.0). Placing equipment in the 'valleys' of these waves is the key to good setup.")
        eff_spk_x, eff_spk_y, eff_spk_z = 0.0, 0.0, 0.0
        eff_Rx, eff_Ry, eff_Rz = 1.0, 1.0, 1.0
        trace_spk = go.Scatter3d(x=[0], y=[0], z=[0], mode='markers', marker=dict(size=8, color='black', symbol='square', line=dict(color='white', width=2)), name="Source (0,0,0)")
        trace_mic = go.Scatter3d(x=[mic_x], y=[mic_y], z=[mic_z], mode='markers', marker=dict(size=8, color='red', symbol='diamond', line=dict(color='white', width=2)), name="Mic (Current)")
    else:
        st.info("💡 **Standing Wave Visualization Mode**: Renders the energy distribution of the entire space affected by the equipment coordinates and sound absorption (reflection) determined in the placement mode.")
        eff_spk_x, eff_spk_y, eff_spk_z = spk_x, spk_y, spk_z
        eff_Rx, eff_Ry, eff_Rz = Rx, Ry, Rz
        trace_spk = go.Scatter3d(x=[spk_x], y=[spk_y], z=[spk_z], mode='markers', marker=dict(size=8, color='blue', symbol='square', line=dict(color='white', width=2)), name="Speaker")
        trace_mic = go.Scatter3d(x=[mic_x], y=[mic_y], z=[mic_z], mode='markers', marker=dict(size=8, color='red', symbol='diamond', line=dict(color='white', width=2)), name="Mic")

    X_flat, Y_flat, Z_flat, tensor_abs = compute_tensor_3d(Lx, Ly, Lz, eff_spk_x, eff_spk_y, eff_spk_z, eff_Rx, eff_Ry, eff_Rz)
    global_min = np.min(tensor_abs)
    global_max = np.percentile(tensor_abs, 98)

    fig_vol = go.Figure()
    fig_vol.add_trace(draw_room_wireframe(Lx, Ly, Lz))
    fig_vol.add_trace(trace_spk)
    fig_vol.add_trace(trace_mic)

    # 1. 初期値の丸め
    initial_val = np.round(tensor_abs[0].flatten(), 2)
    fig_vol.add_trace(go.Volume(
        x=X_flat, y=Y_flat, z=Z_flat, value=initial_val,
        isomin=np.percentile(initial_val, 60), isomax=global_max,
        opacity=0.3, opacityscale=[[-0.5, 0], [0, 0.2], [1, 1]],
        surface_count=12,
        colorscale='RdYlBu_r', cmin=global_min, cmax=global_max,
        caps=dict(x_show=False, y_show=False, z_show=False), name="Sound Pressure"
    ))

    frames = []
    for i, f in enumerate(FREQS_3D):
        val = tensor_abs[i].flatten().astype(np.float32)
        frames.append(go.Frame(
            data=[go.Volume(
                value=val,
                isomin=np.percentile(val, 60), isomax=global_max,
                opacity=0.3, opacityscale=[[-0.5, 0], [0, 0.2], [1, 1]],
                surface_count=12,
                colorscale='RdYlBu_r', cmin=global_min, cmax=global_max,
                caps=dict(x_show=False, y_show=False, z_show=False)
            )],
            traces=[3], 
            name=str(f)
        ))
    fig_vol.frames = frames

    fig_vol.update_layout(
        scene=dict(xaxis_title='X', yaxis_title='Y', zaxis_title='Z', aspectmode='data'),
        margin=dict(l=0, r=0, b=0, t=30), height=700, showlegend=False,
        updatemenus=[dict(
            type="buttons", x=0.05, y=0,
            buttons=[dict(label="Play", method="animate", 
                          args=[None, dict(frame=dict(duration=500, redraw=True), transition=dict(duration=0), fromcurrent=True)])]
        )],
        sliders=[dict(
            active=0, yanchor="top", xanchor="left", currentvalue=dict(font=dict(size=16), prefix="Frequency: ", suffix=" Hz"),
            transition=dict(duration=0),
            pad=dict(b=10, t=50), len=0.9, x=0.15, y=0,
            steps=[dict(args=[[str(f)], dict(frame=dict(duration=300, redraw=True), mode="immediate", transition=dict(duration=0))], # ★ ここも無効化
                        label=str(f), method="animate") for f in FREQS_3D]
        )]
    )
    st.plotly_chart(fig_vol, width='stretch')