import streamlit as st
from PIL import Image
import numpy as np
import requests
import pandas as pd
import io

def main():
    st.title("Leitor de QRCode - Boletim de Urna Eletrônica")

    # Opções de entrada: Upload de imagem
    option = st.selectbox("Escolha o método para ler o QR Code:", ("Upload de imagem",))

    if option == "Upload de imagem":
        run_image_upload()

# Função para upload de uma imagem contendo o QR Code
def run_image_upload():
    uploaded_file = st.file_uploader("Envie uma imagem com QR Code", type=["jpg", "jpeg", "png"])

    if uploaded_file is not None:
        # Abrir a imagem carregada
        image = Image.open(uploaded_file)
        st.image(image, caption="Imagem carregada", use_column_width=True)

        # Converter a imagem para o formato PNG para enviar à API
        image.save("temp_image.png", "PNG")

        # Enviar a imagem para a API zxing e decodificar o QR Code
        qr_data = decode_qr_code("temp_image.png")
        if qr_data:
            st.success("QR Code detectado:")
            data_dict = display_qr_data(qr_data)
            if data_dict:
                display_custom_table(data_dict)
                generate_excel(data_dict)
        else:
            st.warning("Nenhum QR Code detectado na imagem.")

# Função para enviar a imagem para a API zxing e decodificar
def decode_qr_code(image_path):
    url = 'http://api.qrserver.com/v1/read-qr-code/'
    with open(image_path, 'rb') as f:
        files = {'file': f}
        response = requests.post(url, files=files)
    
    if response.status_code == 200:
        json_data = response.json()
        try:
            qr_data = json_data[0]['symbol'][0]['data']
            return qr_data
        except:
            return None
    else:
        return None

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
