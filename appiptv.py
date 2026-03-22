import streamlit as st
import json
import os
from datetime import datetime

SESSION_FILE = "session.json"

# ----------------------
# CONFIG
# ----------------------
st.set_page_config(page_title="Ghost Admin Pro", layout="wide")

USERS_FILE = "users.json"
NEWS_FILE = "news.json"

# ----------------------
# UTILS
# ----------------------
def load_data(file, default):
    if not os.path.exists(file):
        return default
    with open(file, "r") as f:
        try:
            return json.load(f)
        except:
            return default

def save_data(file, data):
    with open(file, "w") as f:
        json.dump(data, f, indent=4)

def is_valid_date(date_text):
    try:
        datetime.strptime(date_text, "%Y-%m-%d %H:%M")
        return True
    except:
        return False

def caducada(caducidad):
    if not caducidad:
        return False
    return datetime.strptime(caducidad, "%Y-%m-%d %H:%M") < datetime.now()

# 🔥 CORREGIDO (minutos reales 0-59)
def tiempo_restante(caducidad):
    if not caducidad or not is_valid_date(caducidad):
        return None, None

    delta = datetime.strptime(caducidad, "%Y-%m-%d %H:%M") - datetime.now()

    if delta.total_seconds() <= 0:
        return 0, 0

    dias = delta.days
    minutos = (delta.seconds % 3600) // 60  # SOLO minutos de la última hora

    return dias, minutos

def save_session(user):
    with open(SESSION_FILE, "w") as f:
        json.dump({"user": user}, f)

def load_session():
    if not os.path.exists(SESSION_FILE):
        return None
    try:
        with open(SESSION_FILE, "r") as f:
            data = json.load(f)
            return data.get("user")
    except:
        return None

def clear_session():
    if os.path.exists(SESSION_FILE):
        os.remove(SESSION_FILE)


# ----------------------
# LOAD DATA
# ----------------------
users = load_data(USERS_FILE, {})
news_list = load_data(NEWS_FILE, [])

for u in users:
    if "password" not in users[u]:
        users[u]["password"] = ""
    if "caducidad" not in users[u]:
        users[u]["caducidad"] = ""

# ----------------------
# SESSION
# ----------------------
if "user" not in st.session_state:
    st.session_state.user = load_session()

# ----------------------
# STYLE
# ----------------------
st.markdown("""
<style>
body { background-color: #0e1117; color: white; }
.card { background-color: #272b33; color: #f0f0f0; padding: 15px; border-radius: 12px; margin-bottom: 10px; }
.alert-card { background-color: #f9d6d5; color: #4d0000; padding: 15px; border-radius: 12px; margin-bottom: 10px; }
.title { font-size: 28px; font-weight: bold; }
.sub-title { font-size: 20px; font-weight: bold; }
button { background-color: #e50914; color: white; border-radius: 5px; }
</style>
""", unsafe_allow_html=True)

# ----------------------
# LOGIN
# ----------------------
def login():
    st.title("🔐 Acceso a Ghost Pro")

    tabs = st.tabs(["Login"])

    with tabs[0]:
        user = st.text_input("Usuario")
        pwd = st.text_input("Contraseña", type="password")

        if st.button("Entrar"):
            if user in users:
                if users[user].get("password") == pwd:
                    st.session_state.user = user
                    save_session(user)
                    st.success("Bienvenido")
                    st.rerun()
                else:
                    st.error("Contraseña incorrecta")
            else:
                st.error("Usuario no existe")

# ----------------------
# DASHBOARD
# ----------------------
def dashboard():
    st.sidebar.title(f"👤 {st.session_state.user}")
    is_admin = st.session_state.user == "admin"

    if is_admin:
        menu = st.sidebar.radio("Menú", ["Inicio", "Foro", "Novedades", "Alertas", "Usuarios Admin", "Logout"])
    else:
        menu = st.sidebar.radio("Menú", ["Inicio", "Foro", "Alertas", "Mi Cuenta", "Logout"])

    # -------- INICIO --------
    if menu == "Inicio":
        st.markdown("<div class='title'>🔥 Novedades</div>", unsafe_allow_html=True)

        novedades = [n for n in news_list if n.get("titulo","") != "ALERTA" and not n.get("titulo","").startswith("Post de")]
        novedades = sorted(novedades, key=lambda x: x.get("fecha",""), reverse=True)

        if len(novedades) == 0:
            st.info("No hay novedades disponibles")

        for n in novedades:
            cad = n.get("caducidad","")
            if caducada(cad):
                continue

            cad_text = f"<br><small>Caduca: {cad}</small>" if cad else ""

            st.markdown(f"""
            <div class='card'>
            <b>{n.get('titulo','Sin título')}</b><br>
            <small>{n.get('fecha','')}</small>
            {cad_text}<br>
            {n.get('contenido','')}
            </div>
            """, unsafe_allow_html=True)

            st.markdown("<br>", unsafe_allow_html=True)

    # -------- FORO --------
    elif menu == "Foro":
        st.subheader("💬 Foro")

        mensaje = st.text_area("Escribe tu mensaje aquí...")

        if st.button("Publicar"):
            if mensaje.strip() != "":
                news_list.append({
                    "titulo": f"Post de {st.session_state.user}",
                    "contenido": mensaje,
                    "fecha": datetime.now().strftime("%Y-%m-%d %H:%M"),
                    "caducidad": "",
                    "forista": st.session_state.user
                })
                save_data(NEWS_FILE, news_list)
                st.success("Publicado")
                st.rerun()

        posts = [n for n in news_list if n.get("titulo","").startswith("Post de") and not caducada(n.get("caducidad",""))]

        for i, n in enumerate(reversed(posts)):
            col1, col2 = st.columns([8,1])

            with col1:
                st.markdown(f"<div class='card'><b>{n.get('titulo','')}</b><br>{n.get('contenido','')}</div>", unsafe_allow_html=True)

            with col2:
                if is_admin:
                    if st.button("❌", key=f"del_post_{i}"):
                        news_list.remove(n)
                        save_data(NEWS_FILE, news_list)
                        st.rerun()

    # -------- NOVEDADES ADMIN --------
    elif menu == "Novedades" and is_admin:
        st.subheader("📰 Crear Novedad")

        titulo = st.text_input("Título")
        contenido = st.text_area("Contenido")
        caducidad = st.text_input("Fecha caducidad (YYYY-MM-DD HH:MM)")

        if st.button("Crear Novedad"):
            if titulo.strip() and contenido.strip():
                news_list.append({
                    "titulo": titulo,
                    "contenido": contenido,
                    "fecha": datetime.now().strftime("%Y-%m-%d %H:%M"),
                    "caducidad": caducidad if is_valid_date(caducidad) else ""
                })
                save_data(NEWS_FILE, news_list)
                st.success("Novedad creada")
                st.rerun()
        # 🔥 LISTA DE NOVEDADES CON BORRADO
        st.subheader("📰 Novedades actuales")

        novedades = [n for n in news_list if n.get("titulo","") != "ALERTA" and not n.get("titulo","").startswith("Post de")]
        novedades = sorted(novedades, key=lambda x: x.get("fecha",""), reverse=True)
        for i, n in enumerate(novedades):
            cad = n.get("caducidad","")
            if caducada(cad):
                continue

            cad_text = f"<br><small>Caduca: {cad}</small>" if cad else ""

            col1, col2 = st.columns([8,1])

            with col1:
                st.markdown(f"<div class='card'><b>{n.get('titulo','Sin título')}</b><br>{n.get('contenido','')}{cad_text}</div>", unsafe_allow_html=True)
                

            with col2:
                if st.button("Eliminar❌", key=f"del_novedad_{i}"):
                    news_list.remove(n)
                    save_data(NEWS_FILE, news_list)
                    st.rerun()

        # -------- ALERTAS --------
    elif menu == "Alertas":
        st.subheader("🚨 Alertas")

        alertas = [n for n in news_list if n.get("titulo","") == "ALERTA" and not caducada(n.get("caducidad",""))]
        alertas = sorted(alertas, key=lambda x: x.get("fecha",""), reverse=True)

        if len(alertas) == 0:
            st.info("No hay alertas activas")

        for n in alertas:
            cad = n.get("caducidad","")
            cad_text = f"<br><small>Caduca: {cad}</small>" if cad else ""

            st.markdown(f"""
        <div class='alert-card'>
        <b>🚨 ALERTA</b>
        <br>
        <small>{n.get('fecha','')}</small>

        <br><br>

        <div style='margin-top:5px;'>
        {n.get("contenido","")}
        </div>

        {cad_text}
        </div>
        """, unsafe_allow_html=True)
        
        if is_admin:
            st.subheader("🚨 Crear Alerta")
            
            contenido = st.text_area("Contenido de la alerta")
            caducidad = st.text_input("Fecha caducidad (YYYY-MM-DD HH:MM)")

            if st.button("Crear Alerta"):
                if contenido.strip():
                    news_list.append({
                        "titulo": "ALERTA",
                        "contenido": contenido,
                        "fecha": datetime.now().strftime("%Y-%m-%d %H:%M"),
                        "caducidad": caducidad if is_valid_date(caducidad) else ""
                    })
                    save_data(NEWS_FILE, news_list)
                    st.success("Alerta creada")
                    st.rerun() 
            if is_admin:
                st.subheader("🚨 Alertas actuales")
            
            for i, n in enumerate(news_list):
                if n.get("titulo","") != "ALERTA" or caducada(n.get("caducidad","")):
                    continue
                
                cad = n.get("caducidad","")
                
                col1, col2, col3 = st.columns([8,1,1])
                with col1: 
                    st.markdown(alertas[i].get("contenido",""), unsafe_allow_html=True)
                with col2:
                    if st.button("Eliminar❌", key=f"del_alerta_{i}"):
                        del news_list[i]
                        save_data(NEWS_FILE, news_list)
                        st.success("Alerta eliminada")
                        st.rerun()
                
                        
                with col3: # EDITAR SOLO CONTENIDO, NO CADUCIDAD
                    if st.button("Editar✏️", key=f"edit_alerta_{i}"): 
                        st.session_state.editing_alerta = i
                        st.session_state.editing_alerta_content = n.get("contenido","")
                        st.rerun()
                
                # Formulario de edición
                if st.session_state.get("editing_alerta") == i:
                    new_content = st.text_area("Nuevo contenido", value=st.session_state.get("editing_alerta_content",""), key=f"edit_content_{i}")
                    if st.button("Guardar", key=f"save_alerta_{i}"):
                        news_list[i]["contenido"] = new_content
                        save_data(NEWS_FILE, news_list)
                        st.success("Alerta actualizada")
                        st.session_state.editing_alerta = None
                        st.session_state.editing_alerta_content = ""
                        st.rerun()
        
        

                        # -------- USUARIOS ADMIN --------
    elif menu == "Usuarios Admin" and is_admin:
        for u in list(users.keys()):
            if u == "admin":
                st.write("admin (admin)")
                continue

            col1, col2, col3 = st.columns([6,1,1])

        
            with col1:
                st.write(f"{u} ({users[u].get('caducidad','Sin caducidad')})")
            with col2:
                if st.button("Editar✏️", key=f"edit_{u}"):
                    new_cad = st.text_input(f"Caducidad para {u} (YYYY-MM-DD HH:MM)", key=f"cad_{u}")
                    if st.button("Guardar", key=f"save_{u}"):
                        if new_cad.strip() == "" or is_valid_date(new_cad):
                            users[u]["caducidad"] = new_cad.strip()
                            save_data(USERS_FILE, users)
                            st.success("Usuario actualizado")
                            st.rerun()
                        else:
                            st.error("Fecha no válida")
            with col3:
                if st.button("Eliminar❌", key=f"del_{u}"):
                    del users[u]
                    save_data(USERS_FILE, users)
                    st.success("Usuario eliminado")
                    st.rerun()
        st.subheader("Crear nuevo usuario")
        new_user = st.text_input("Nombre de usuario", key="new_user")
        new_pass = st.text_input("Contraseña", type="password", key="new_pass")
        new_cad = st.text_input("Caducidad (YYYY-MM-DD HH:MM)", key="new_cad")
        if st.button("Crear"):
            if new_user.strip() and new_pass.strip():
                if new_user in users:
                    st.error("El usuario ya existe")
                else:
                    users[new_user] = {
                        "password": new_pass.strip(),
                        "caducidad": new_cad.strip() if is_valid_date(new_cad) else ""
                    }
                    save_data(USERS_FILE, users)
                    st.success("Usuario creado")
                    st.rerun()
            else:
                st.error("Usuario y contraseña son obligatorios")

    # -------- MI CUENTA --------
    elif menu == "Mi Cuenta" and not is_admin:
        st.subheader("📋 Mi Cuenta")

        cad = users[st.session_state.user].get("caducidad","")
        dias, minutos = tiempo_restante(cad)

        if dias is not None:
            st.write("Tu cuenta tiene una fecha de caducidad.")
            st.write(f"Te quedan {dias} días y {minutos} minutos de acceso.")
        else:
            st.write("Tu cuenta no tiene fecha de caducidad.")
            st.write("Disfruta de tu acceso ilimitado.")

        if caducada(cad):
            st.error("Tu cuenta ha caducado. Contacta al administrador.")

    # -------- LOGOUT --------
    elif menu == "Logout":
        st.session_state.user = None
        clear_session()
        st.rerun()

# ----------------------
# MAIN
# ----------------------
if st.session_state.user:
    dashboard()
else:
    login()
