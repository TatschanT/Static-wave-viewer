import streamlit as st
import numpy as np
import plotly.graph_objects as go

st.set_page_config(page_title="Standing Wave Viewer V0.7 (Golden Master)", layout="wide")
st.title("🎵 Standing Wave Viewer V0.7 (Unified Calculation Modes)")

# ==========================================
# UI: Sidebar (Common Settings)
# ==========================================
st.sidebar.title("Control Panel")

source_mode = st.sidebar.radio("Sound Source Setup", [
    "🔊 1 Source (Mono)",
    "🔊🔊 2 Sources (Stereo)"
])
num_sources = 1 if "1 Source" in source_mode else 2

if num_sources == 2:
    corr_mode = st.sidebar.radio("L/R Bass Signal Correlation", [
        "🔀 Uncorrelated (Independent Power Sum)",
        "🔗 In-Phase (Global Cancel - Fast)",
        "🌊 In-Phase (True Complex Field - Realistic)"
    ], help="Uncorrelated: adds power. Global Cancel: Fast approximation for cancel. True Complex: Real-world spatial interference.")
else:
    # モノラルモード時は計算負荷の軽い近似モード（パワー加算相当）をデフォルトにする
    corr_mode = "Mono (Approx)"

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
spk_x = st.sidebar.slider("Spk 1 (L) X" if num_sources==2 else "Speaker X", 0.0, Lx, 0.5, 0.01)
spk_y = st.sidebar.slider("Spk 1 (L) Y" if num_sources==2 else "Speaker Y", 0.0, Ly, 0.5, 0.01)
spk_z = st.sidebar.slider("Spk 1 (L) Z" if num_sources==2 else "Speaker Z", 0.0, Lz, 0.5, 0.01)

if num_sources == 2:
    spk2_x = st.sidebar.slider("Spk 2 (R) X", 0.0, Lx, Lx - 0.5, 0.01)
    spk2_y = st.sidebar.slider("Spk 2 (R) Y", 0.0, Ly, 0.5, 0.01)
    spk2_z = st.sidebar.slider("Spk 2 (R) Z", 0.0, Lz, 0.5, 0.01)
else:
    spk2_x, spk2_y, spk2_z = spk_x, spk_y, spk_z

mic_x = st.sidebar.slider("Mic X", 0.0, Lx, Lx/2, 0.01)
mic_y = st.sidebar.slider("Mic Y", 0.0, Ly, Ly/2, 0.01)
mic_z = st.sidebar.slider("Mic Z", 0.0, Lz, Lz/2, 0.01)

with st.sidebar.expander("🧱 Wall Reflection Coefficients"):
    Rx1 = st.slider("Left Wall (X=0)", 0.0, 1.0, 0.80, 0.05)
    Rx2 = st.slider("Right Wall (X=Lx)", 0.0, 1.0, 0.80, 0.05)
    Ry1 = st.slider("Front Wall (Y=0)", 0.0, 1.0, 0.80, 0.05)
    Ry2 = st.slider("Back Wall (Y=Ly)", 0.0, 1.0, 0.80, 0.05)
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

def calc_shape(n, pos, L, R):
    if n == 0: return pos * 0.0 + 1.0
    return np.sqrt(1 + R**2 + 2 * R * np.cos(2 * n * np.pi * pos / L)) / (1 + R)

def get_psi(n, pos, L, R):
    if n == 0: return 1.0 + 0j
    theta = n * np.pi * pos / L
    return np.cos(theta) - 1j * ((1 - R) / (1 + R)) * np.sin(theta)

def calc_gamma(nx, ny, nz, Rx, Ry, Rz):
    n_sum = nx + ny + nz
    if n_sum == 0: return 5.0
    R_eff = (nx * Rx + ny * Ry + nz * Rz) / n_sum
    return 3.0 + 40.0 * (1.0 - R_eff)

@st.cache_data(show_spinner=False)
def compute_f_response_1d(Lx, Ly, Lz, num_src, corr_mode, sx, sy, sz, sx2, sy2, sz2, mx, my, mz, Rx, Ry, Rz):
    max_nx, max_ny, max_nz = get_max_modes(Lx, Ly, Lz)
    tensor_1d = np.zeros(len(FREQS_1D))

    if "True Complex Field" in corr_mode:
        # V0.6 複素数合成
        for i, f_query in enumerate(FREQS_1D):
            P_complex_1 = 0j
            P_complex_2 = 0j

            for nx in range(max_nx):
                for ny in range(max_ny):
                    for nz in range(max_nz):
                        if nx == 0 and ny == 0 and nz == 0: continue
                        fn = (SPEED_OF_SOUND / 2.0) * np.sqrt((nx/Lx)**2 + (ny/Ly)**2 + (nz/Lz)**2)
                        if fn > 250: continue

                        gamma = calc_gamma(nx, ny, nz, Rx, Ry, Rz)
                        res_complex = (50.0 / fn) / ((f_query - fn) + 1j * gamma)

                        psi1 = get_psi(nx, sx, Lx, Rx) * get_psi(ny, sy, Ly, Ry) * get_psi(nz, sz, Lz, Rz)
                        rec_psi = get_psi(nx, mx, Lx, Rx) * get_psi(ny, my, Ly, Ry) * get_psi(nz, mz, Lz, Rz)

                        P_complex_1 += psi1 * rec_psi * res_complex

                        if num_src == 2:
                            psi2 = get_psi(nx, sx2, Lx, Rx) * get_psi(ny, sy2, Ly, Ry) * get_psi(nz, sz2, Lz, Rz)
                            P_complex_2 += psi2 * rec_psi * res_complex
            
            # ステレオ完全複素合成時は In-Phase
            tensor_1d[i] = np.abs(P_complex_1 + P_complex_2)
    else:
        # V0.5 近似（Mono / Uncorrelated / Global Cancel）
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
                        else: # Uncorrelated
                            exc = np.sqrt(np.abs(psi1)**2 + np.abs(psi2)**2) / 2.0
                    else:
                        exc = np.abs(psi1)

                    rec = calc_shape(nx, mx, Lx, Rx) * calc_shape(ny, my, Ly, Ry) * calc_shape(nz, mz, Lz, Rz)
                    gamma = calc_gamma(nx, ny, nz, Rx, Ry, Rz)

                    for i, f in enumerate(FREQS_1D):
                        res_amp = (50.0 / fn) / np.sqrt((f - fn)**2 + gamma**2)
                        tensor_1d[i] += (exc * rec * res_amp) ** 2

        tensor_1d = np.sqrt(tensor_1d)

    f_response_db = 20 * np.log10(np.clip(tensor_1d, 1e-10, None))
    f_response_db = f_response_db - np.max(f_response_db)
    return f_response_db

@st.cache_data(show_spinner="Calculating spatial tensor...")
def compute_tensor_3d(Lx, Ly, Lz, num_src, corr_mode, sx, sy, sz, sx2, sy2, sz2, Rx, Ry, Rz):
    x = np.linspace(0, Lx, 32)
    y = np.linspace(0, Ly, 32)
    z = np.linspace(0, Lz, 32)
    X, Y, Z = np.meshgrid(x, y, z, indexing='ij')

    tensor = np.zeros((len(FREQS_3D), len(x), len(y), len(z)))
    max_nx, max_ny, max_nz = get_max_modes(Lx, Ly, Lz)

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

                        gamma = calc_gamma(nx, ny, nz, Rx, Ry, Rz)
                        res_complex = (50.0 / fn) / ((f_query - fn) + 1j * gamma)

                        mode_complex = get_psi(nx, X, Lx, Rx) * get_psi(ny, Y, Ly, Ry) * get_psi(nz, Z, Lz, Rz)
                        psi1 = get_psi(nx, sx, Lx, Rx) * get_psi(ny, sy, Ly, Ry) * get_psi(nz, sz, Lz, Rz)

                        P_complex_1 += psi1 * mode_complex * res_complex

                        if num_src == 2:
                            psi2 = get_psi(nx, sx2, Lx, Rx) * get_psi(ny, sy2, Ly, Ry) * get_psi(nz, sz2, Lz, Rz)
                            P_complex_2 += psi2 * mode_complex * res_complex

            tensor[i] = np.abs(P_complex_1 + P_complex_2)
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
                        else: # Uncorrelated
                            exc = np.sqrt(np.abs(psi1)**2 + np.abs(psi2)**2) / 2.0
                    else:
                        exc = np.abs(psi1)

                    mode_shape = calc_shape(nx, X, Lx, Rx) * calc_shape(ny, Y, Ly, Ry) * calc_shape(nz, Z, Lz, Rz)
                    gamma = calc_gamma(nx, ny, nz, Rx, Ry, Rz)

                    for i, f in enumerate(FREQS_3D):
                        res_amp = (50.0 / fn) / np.sqrt((f - fn)**2 + gamma**2)
                        tensor[i] += (exc * mode_shape * res_amp) ** 2
        
        tensor = np.sqrt(tensor)

    return X.flatten(), Y.flatten(), Z.flatten(), tensor

def draw_room_wireframe(Lx, Ly, Lz):
    x_lines = [0, Lx, Lx, 0, 0, 0, Lx, Lx, 0, 0, None, Lx, Lx, None, Lx, Lx, None, 0, 0]
    y_lines = [0, 0, Ly, Ly, 0, 0, 0, Ly, Ly, 0, None, 0, 0, None, Ly, Ly, None, Ly, Ly]
    z_lines = [0, 0, 0, 0, 0, Lz, Lz, Lz, Lz, Lz, None, 0, Lz, None, 0, Lz, None, 0, Lz]
    return go.Scatter3d(x=x_lines, y=y_lines, z=z_lines, mode='lines', line=dict(color='gray', width=3), name="Room", hoverinfo='skip')

# ==========================================
# Rendering
# ==========================================
if num_sources == 2:
    spk_xs, spk_ys, spk_zs = [spk_x, spk2_x], [spk_y, spk2_y], [spk_z, spk2_z]
else:
    spk_xs, spk_ys, spk_zs = [spk_x], [spk_y], [spk_z]

if mode == "🎛️ 1. Layout Placement (Ultra-fast)":
    st.info("💡 **Layout Placement Mode**: Adjust coordinates.")
    col1, col2 = st.columns([5, 5])

    trace_spk = go.Scatter3d(x=spk_xs, y=spk_ys, z=spk_zs, mode='markers', marker=dict(size=8, color='blue', symbol='square', line=dict(color='white', width=2)), name="Speaker(s)")
    trace_mic = go.Scatter3d(x=[mic_x], y=[mic_y], z=[mic_z], mode='markers', marker=dict(size=8, color='red', symbol='diamond', line=dict(color='white', width=2)), name="Mic")

    with col1:
        fig_layout = go.Figure(data=[draw_room_wireframe(Lx, Ly, Lz), trace_spk, trace_mic])
        fig_layout.update_layout(
            scene=dict(xaxis=dict(range=[-0.5, Lx+0.5]), yaxis=dict(range=[-0.5, Ly+0.5]), zaxis=dict(range=[-0.5, Lz+0.5]), aspectmode='data'),
            margin=dict(l=0, r=0, b=0, t=30), height=500, title="3D Equipment Layout"
        )
        st.plotly_chart(fig_layout, width='stretch')

    with col2:
        f_response_db = compute_f_response_1d(Lx, Ly, Lz, num_sources, corr_mode, spk_x, spk_y, spk_z, spk2_x, spk2_y, spk2_z, mic_x, mic_y, mic_z, Rx, Ry, Rz)
        fig_f = go.Figure(data=[go.Scatter(x=FREQS_1D, y=f_response_db, mode='lines+markers', line=dict(color='red', width=2))])
        fig_f.update_layout(
            xaxis_title="Frequency (Hz)", yaxis_title="Relative SPL (dB)",
            yaxis=dict(range=[-25, 2]),
            margin=dict(l=0, r=0, b=0, t=30), height=500, title="Frequency Response (Max Peak = 0dB)"
        )
        st.plotly_chart(fig_f, width='stretch')

else:
    if mode == "📐 3. Room Bare Specs (Rigid/Corner)":
        eff_num_sources = 1
        eff_corr = "Mono"
        eff_spk_x, eff_spk_y, eff_spk_z = 0.0, 0.0, 0.0
        eff_spk2_x, eff_spk2_y, eff_spk2_z = 0.0, 0.0, 0.0
        eff_Rx, eff_Ry, eff_Rz = 1.0, 1.0, 1.0
        spk_plot_x, spk_plot_y, spk_plot_z = [0.0], [0.0], [0.0]

        trace_spk = go.Scatter3d(x=spk_plot_x, y=spk_plot_y, z=spk_plot_z, mode='markers', marker=dict(size=8, color='black', symbol='square', line=dict(color='white', width=2)), name="Source (Corner)")
        trace_mic = go.Scatter3d(x=[mic_x], y=[mic_y], z=[mic_z], mode='markers', marker=dict(size=8, color='red', symbol='diamond', line=dict(color='white', width=2)), name="Mic (Current)")
    else:
        eff_num_sources = num_sources
        eff_corr = corr_mode
        eff_spk_x, eff_spk_y, eff_spk_z = spk_x, spk_y, spk_z
        eff_spk2_x, eff_spk2_y, eff_spk2_z = spk2_x, spk2_y, spk2_z
        eff_Rx, eff_Ry, eff_Rz = Rx, Ry, Rz
        trace_spk = go.Scatter3d(x=spk_xs, y=spk_ys, z=spk_zs, mode='markers', marker=dict(size=8, color='blue', symbol='square', line=dict(color='white', width=2)), name="Speaker(s)")
        trace_mic = go.Scatter3d(x=[mic_x], y=[mic_y], z=[mic_z], mode='markers', marker=dict(size=8, color='red', symbol='diamond', line=dict(color='white', width=2)), name="Mic")

    X_flat, Y_flat, Z_flat, tensor_abs = compute_tensor_3d(Lx, Ly, Lz, eff_num_sources, eff_corr, eff_spk_x, eff_spk_y, eff_spk_z, eff_spk2_x, eff_spk2_y, eff_spk2_z, eff_Rx, eff_Ry, eff_Rz)
    global_min = np.min(tensor_abs)
    global_max = np.percentile(tensor_abs, 98)

    fig_vol = go.Figure()
    fig_vol.add_trace(draw_room_wireframe(Lx, Ly, Lz))
    fig_vol.add_trace(trace_spk)
    fig_vol.add_trace(trace_mic)

    initial_val = tensor_abs[0].flatten().astype(np.float32)
    fig_vol.add_trace(go.Volume(
        x=X_flat, y=Y_flat, z=Z_flat, value=initial_val,
        isomin=np.percentile(initial_val, 60), isomax=global_max,
        opacity=0.3, opacityscale=[[-0.5, 0], [0, 0.2], [1, 1]],
        surface_count=12, colorscale='RdYlBu_r', cmin=global_min, cmax=global_max,
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
                surface_count=12, colorscale='RdYlBu_r', cmin=global_min, cmax=global_max,
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
            buttons=[dict(label="Play", method="animate", args=[None, dict(frame=dict(duration=500, redraw=True), transition=dict(duration=0), fromcurrent=True)])]
        )],
        sliders=[dict(
            active=0, yanchor="top", xanchor="left", currentvalue=dict(font=dict(size=16), prefix="Frequency: ", suffix=" Hz"),
            transition=dict(duration=0), pad=dict(b=10, t=50), len=0.9, x=0.15, y=0,
            steps=[dict(args=[[str(f)], dict(frame=dict(duration=300, redraw=True), mode="immediate", transition=dict(duration=0))],
            label=str(f), method="animate") for f in FREQS_3D]
        )]
    )

    st.plotly_chart(fig_vol, width='stretch')