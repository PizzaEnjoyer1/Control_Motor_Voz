import os
import streamlit as st
from bokeh.models.widgets import Button
from bokeh.models import CustomJS
from streamlit_bokeh_events import streamlit_bokeh_events
import paho.mqtt.client as paho
import json
from googletrans import Translator

def on_publish(client, userdata, result):  # Callback
    print("El dato ha sido publicado \n")
    pass

def on_message(client, userdata, message):
    global message_received
    message_received = str(message.payload.decode("utf-8"))
    st.write(message_received)  # Muestra el mensaje en Streamlit

broker = "broker.mqttdashboard.com"
port = 1883
client1 = paho.Client("MOTOR_WEB_APP_VOICE")  # Cambiar
client1.on_message = on_message
client1.connect(broker, port)
client1.subscribe("CONTROL_VOZ")
client1.loop_start()  # Comienza el bucle del cliente MQTT

st.title("Interfaces Multimodales")
st.subheader("CONTROL POR VOZ")

st.write("Toca el Botón y habla ")

stt_button = Button(label=" Inicio ", width=200)

stt_button.js_on_event("button_click", CustomJS(code="""
    var recognition = new webkitSpeechRecognition();
    recognition.continuous = true;
    recognition.interimResults = true;

    recognition.onresult = function (e) {
        var value = "";
        for (var i = e.resultIndex; i < e.results.length; ++i) {
            if (e.results[i].isFinal) {
                value += e.results[i][0].transcript;
            }
        }
        if (value != "") {
            document.dispatchEvent(new CustomEvent("GET_TEXT", { detail: value }));
        }
    }
    recognition.start();
"""))

result = streamlit_bokeh_events(
    stt_button,
    events="GET_TEXT",
    key="listen",
    refresh_on_update=False,
    override_height=75,
    debounce_time=0)

if result:
    if "GET_TEXT" in result:
        recognized_text = result.get("GET_TEXT").strip()
        st.write("Texto escuchado:", recognized_text)

        # Procesar el texto recibido y verificar el idioma y la confianza
        translator = Translator()
        detected_language = translator.detect(recognized_text)
        language_name = detected_language.lang
        confidence = detected_language.confidence * 100  # Convertir a porcentaje

        if language_name == 'es':
            st.write("Idioma reconocido: Español")
        else:
            st.write(f"Idioma reconocido: {language_name}")

        st.write(f"Nivel de confianza: {confidence:.2f}%")  # Muestra el nivel de confianza

        # Publicar el mensaje en MQTT
        client1.on_publish = on_publish
        message = json.dumps({"Act1": recognized_text.strip()})
        ret = client1.publish("CONTROL_VOZ", message)

    # Mostrar mensajes de comandos no reconocidos
