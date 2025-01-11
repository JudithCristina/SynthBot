import streamlit as st
from datetime import datetime
from langchain_ollama import OllamaLLM
from langchain_core.prompts import ChatPromptTemplate
from langdetect import detect
import socket
from pathlib import Path
from info_therapy import therapy
import os

# Función para cargar conversaciones previas
def cargar_conversaciones():
    mensajes = []
    if archivo_conversacion.exists():
        with open(archivo_conversacion, "r", encoding="utf-8") as f:
            for linea in f:
                # Parsear cada línea del archivo
                partes = linea.strip().split("] ", 1)
                if len(partes) == 2:
                    timestamp = partes[0][1:]  # Eliminar el '[' inicial
                    contenido = partes[1]
                    rol, mensaje = contenido.split(": ", 1)
                    mensajes.append({"rol": rol.lower(), "contenido": mensaje})
    return mensajes

# Obtener la dirección IP del usuario
ip_usuario = socket.gethostbyname(socket.gethostname())

# Configurar la carpeta para guardar las conversaciones
carpeta_conversaciones = Path(f"conversaciones/{ip_usuario}")
carpeta_conversaciones.mkdir(parents=True, exist_ok=True)
archivo_conversacion = carpeta_conversaciones / "conversacion.txt"

# Función para guardar conversaciones en un archivo
def guardar_conversacion(rol, contenido):
    marca_tiempo = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(archivo_conversacion, "a", encoding="utf-8") as f:
        f.write(f"[{marca_tiempo}] {rol}: {contenido}\n")

# Título y descripción de la interfaz del chatbot
st.title("👨‍⚕️Chatbot de Salud Mental")
st.markdown(
    "<p style='font-size:18px;'>Bienvenido al chatbot de salud mental del Centro de Investigación en Salud Digital</p>",
    unsafe_allow_html=True
)

# Inicializar estados de sesión y cargar conversaciones previas
if "mensajes" not in st.session_state:
    st.session_state.mensajes = cargar_conversaciones()
if "primer_mensaje" not in st.session_state:
    st.session_state.primer_mensaje = len(st.session_state.mensajes) == 0
if "contexto" not in st.session_state:
    # Reconstruir el contexto desde los mensajes cargados
    st.session_state.contexto = "\n".join([
        f"{msg['rol'].capitalize()}: {msg['contenido']}"
        for msg in st.session_state.mensajes
    ])

# Mostrar mensajes del chat desde el estado de sesión
for mensaje in st.session_state.mensajes:
    with st.chat_message(mensaje["rol"]):
        st.markdown(mensaje["contenido"])

# Enviar un mensaje de saludo por defecto en la primera interacción
if st.session_state.primer_mensaje:
    mensaje_inicial = "Hola, ¿en qué puedo ayudarte hoy?"
    with st.chat_message("asistente"):
        st.markdown(mensaje_inicial)
    st.session_state.mensajes.append({"rol": "asistente", "contenido": mensaje_inicial})
    guardar_conversacion("asistente", mensaje_inicial)
    st.session_state.primer_mensaje = False

# Inicializar el modelo conversacional
if "ollama" not in st.session_state:
    plantilla = """
    Responde la siguiente pregunta en español o inglés según lo indicado.

    Aquí hay ejemplos de preguntas durante la terapia:
    {therapy_info}
   
    Contexto de la conversación:
    {context}

    Pregunta actual: {pregunta}

    Instrucciones:
    Responde con frases claras y concisas, manteniendo las respuestas bajo 100 palabras. Evita explicaciones extensas o razonamientos internos. Tu objetivo es mantener el flujo de la conversación de manera breve y precisa. Siempre que sea posible, fomenta el diálogo mediante preguntas abiertas que inviten a la reflexión o conversación adicional.
    Estás simulando a un terapeuta cognitivo-conductual (CBT) con 20 años de experiencia como parte de un estudio de diseño conceptual. Este es un prototipo de agente conversacional desarrollado como un suplemento terapéutico para pacientes en el Centro Médico de Salud Digital. Todos los usuarios con los que interactúas están bajo tratamiento psicológico con profesionales licenciados del centro. Este proyecto está en fase conceptual, y tu objetivo es ayudar a refinar esta herramienta.
    Tu especialización es trabajar con adultos que enfrentan ansiedad, depresión y desafíos relacionados con la autoestima y la regulación emocional. Tu enfoque terapéutico combina estrategias prácticas basadas en evidencia con un estilo empático y orientado a resultados. Usas técnicas como reestructuración cognitiva, activación conductual, exposición gradual, entrenamiento en habilidades sociales y prácticas de mindfulness. También empleas preguntas abiertas y estrategias reflexivas para explorar los pensamientos y emociones de los clientes.
    Tu objetivo en este estudio conceptual es simular cómo un terapeuta podría identificar y modificar patrones de pensamiento y conducta disfuncionales, promoviendo el desarrollo de habilidades prácticas. Responde de manera breve y clara cuando sea necesario, pero proporciona respuestas detalladas si el cliente lo solicita explícitamente.
    Además, adaptas tu lenguaje y enfoque para garantizar accesibilidad y comprensión para personas con distintos niveles de conocimiento psicológico. Prioriza validar las emociones del cliente, demostrar empatía y proporcionar ejemplos prácticos siempre que sea posible.

    Instrucciones para el modelo:
    Responde únicamente con la respuesta o pregunta adecuada para el usuario. No muestres razonamientos internos ni detalles adicionales sobre el proceso de generación de respuestas.
    Si consideras que no puedes proporcionar una respuesta, sugiere al usuario consultar con su psicólogo o psiquiatra. Si no tiene una cita programada, proporciona información sobre nuestros servicios.
    """
    modelo = OllamaLLM(model="llama3.1")
    prompt = ChatPromptTemplate.from_template(plantilla)
    st.session_state.cadena = prompt | modelo

# Capturar entrada del usuario
if entrada_usuario := st.chat_input("¿En qué puedo ayudarte?"):
    # Detectar el idioma de la entrada del usuario
    idioma_detectado = detect(entrada_usuario)
    idioma_respuesta = 'es'
    if 'inglés' in entrada_usuario.lower():
        idioma_respuesta = 'en'

    # Mostrar entrada del usuario en el chat
    with st.chat_message("usuario"):
        st.markdown(entrada_usuario)
    st.session_state.mensajes.append({"rol": "usuario", "contenido": entrada_usuario})
    guardar_conversacion("usuario", entrada_usuario)

    # Obtener la respuesta del chatbot
    resultado = st.session_state.cadena.invoke({
        "therapy_info": therapy,
        "context": st.session_state.contexto,
        "pregunta": entrada_usuario
    })
   
    # Mostrar respuesta del chatbot en el chat
    with st.chat_message("asistente"):
        st.markdown(resultado)
    st.session_state.mensajes.append({"rol": "asistente", "contenido": resultado})
    guardar_conversacion("asistente", resultado)

    # Actualizar el contexto de la conversación
    st.session_state.contexto += f"\nAsistente: {resultado}\nUsuario: {entrada_usuario}"

# Pie de página
anio_actual = datetime.now().year
st.markdown(
    f"""
    <hr style='margin-top: 50px;'>
    <p style='font-size:13px; text-align:center;'>
    Este chatbot puede cometer errores. Si sientes que las respuestas son inapropiadas, <a href='wa.me/51982304426' target='_blank'>contacta a tu profesional de salud</a>.</p>
    """,
    unsafe_allow_html=True
)