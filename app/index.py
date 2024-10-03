import streamlit as st
import cv2
from pyzbar.pyzbar import decode
from PIL import Image
import numpy as np
import pandas as pd
import io

def main():
    st.title("Leitor de QRCode - Boletim de Urna Eletrônica")

    # Opções de entrada: Webcam, Leitor de código de barras, Upload de arquivo
    option = st.selectbox("Escolha o método para ler o QR Code:", ("Webcam", "Leitor de código de barras", "Upload de imagem"))

    if option == "Webcam":
        run_webcam()

    elif option == "Leitor de código de barras":
        run_barcode_reader()

    elif option == "Upload de imagem":
        run_image_upload()

# Função para capturar o QR Code da webcam
def run_webcam():
    run = st.checkbox('Ativar webcam')
    if run:
        video_capture = cv2.VideoCapture(0)
        stframe = st.empty()

        while run:
            ret, frame = video_capture.read()
            if ret:
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                img = Image.fromarray(frame)
                stframe.image(img)

                # Decodificar o QR Code
                decoded_objects = decode(frame)
                if decoded_objects:
                    for obj in decoded_objects:
                        qr_data = obj.data.decode("utf-8")
                        st.success("QR Code detectado:")
                        data_dict = display_qr_data(qr_data)
                        if data_dict:
                            display_custom_table(data_dict)
                            generate_excel(data_dict)
                        break  # Para evitar múltiplas leituras, parar após o primeiro QRCode detectado

                if not run:
                    break

        video_capture.release()
        cv2.destroyAllWindows()

# Função para ler o QR Code via leitor de código de barras
def run_barcode_reader():
    qr_data = st.text_input("Escaneie o QRCode usando o leitor de código de barras:")
    if qr_data:
        st.success("QR Code detectado:")
        data_dict = display_qr_data(qr_data)
        if data_dict:
            display_custom_table(data_dict)
            generate_excel(data_dict)
    else:
        st.warning("Aguardando leitura do QR Code...")

# Função para upload de uma imagem contendo o QR Code
def run_image_upload():
    uploaded_file = st.file_uploader("Envie uma imagem com QR Code", type=["jpg", "jpeg", "png"])

    if uploaded_file is not None:
        # Abrir a imagem carregada
        image = Image.open(uploaded_file)
        st.image(image, caption="Imagem carregada", use_column_width=True)

        # Converter a imagem para o formato OpenCV
        image_np = np.array(image)
        
        # Decodificar o QR Code
        decoded_objects = decode(image_np)
        if decoded_objects:
            for obj in decoded_objects:
                qr_data = obj.data.decode("utf-8")
                st.success("QR Code detectado:")
                data_dict = display_qr_data(qr_data)
                if data_dict:
                    display_custom_table(data_dict)
                    generate_excel(data_dict)
        else:
            st.warning("Nenhum QR Code detectado na imagem.")

# Função para exibir os dados do QRCode de forma organizada
def display_qr_data(qr_data):
    data_dict = parse_qr_data(qr_data)
    return data_dict

# Função para organizar os dados do QR Code
def parse_qr_data(qr_data):
    qr_info_list = qr_data.split(" ")
    data_dict = {}

    for info in qr_info_list:
        key_value = info.split(":")
        if len(key_value) == 2:
            key, value = key_value
            data_dict[key] = value

    return data_dict

# Função para exibir os dados formatados em uma tabela customizada
def display_custom_table(data_dict):
    st.write("### Informações do Boletim de Urna")
    urna_info = {
        "Identificação da Urna (IDUE)": data_dict.get("IDUE", ""),
        "Município (MUNI)": data_dict.get("MUNI", ""),
        "Zona Eleitoral (ZONA)": data_dict.get("ZONA", ""),
        "Seção Eleitoral (SECA)": data_dict.get("SECA", ""),
        "Data e Hora de Abertura": f"{data_dict.get('DTPL', '')} às {data_dict.get('HRAB', '')}",
        "Data e Hora de Fechamento": f"{data_dict.get('DTFC', '')} às {data_dict.get('HRFC', '')}",
        "Assinatura Digital": data_dict.get("ASSI", "")
    }

    urna_df = pd.DataFrame(urna_info.items(), columns=["Informação", "Valor"])
    st.table(urna_df)

    st.write("### Resultados da Votação")
    candidatos = ['12', '13', '15', '17', '18', '19', '27', '30', '45', '50', '51']
    votos = {f"Candidato {cand}": data_dict.get(cand, "0") for cand in candidatos}
    votos["Total de votos computados"] = data_dict.get("TOTC", "0")

    votos_df = pd.DataFrame(votos.items(), columns=["Candidato", "Votos"])
    st.table(votos_df)

# Função para gerar a planilha Excel e disponibilizar para download
def generate_excel(data_dict):
    urna_info = {
        "Identificação da Urna (IDUE)": data_dict.get("IDUE", ""),
        "Município (MUNI)": data_dict.get("MUNI", ""),
        "Zona Eleitoral (ZONA)": data_dict.get("ZONA", ""),
        "Seção Eleitoral (SECA)": data_dict.get("SECA", ""),
        "Data e Hora de Abertura": f"{data_dict.get('DTPL', '')} às {data_dict.get('HRAB', '')}",
        "Data e Hora de Fechamento": f"{data_dict.get('DTFC', '')} às {data_dict.get('HRFC', '')}",
        "Assinatura Digital": data_dict.get("ASSI", "")
    }

    urna_df = pd.DataFrame(urna_info.items(), columns=["Informação", "Valor"])

    candidatos = ['12', '13', '15', '17', '18', '19', '27', '30', '45', '50', '51']
    votos = {f"Candidato {cand}": data_dict.get(cand, "0") for cand in candidatos}
    votos["Total de votos computados"] = data_dict.get("TOTC", "0")

    votos_df = pd.DataFrame(votos.items(), columns=["Candidato", "Votos"])

    # Criar um buffer em memória para armazenar o arquivo Excel
    output = io.BytesIO()
    writer = pd.ExcelWriter(output, engine='xlsxwriter')

    # Escrever os DataFrames no escritor Excel
    urna_df.to_excel(writer, index=False, sheet_name='Boletim de Urna')
    votos_df.to_excel(writer, index=False, sheet_name='Resultados')

    # Fechar o escritor para garantir que todos os dados foram gravados no buffer
    writer.close()

    # Obter o conteúdo do buffer
    processed_data = output.getvalue()

    # Botão para download do Excel
    st.download_button(
        label="Baixar planilha com os dados",
        data=processed_data,
        file_name="boletim_de_urna.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

if __name__ == '__main__':
    main()
