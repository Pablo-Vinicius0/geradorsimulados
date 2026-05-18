import json
import os
import io
import streamlit as st
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import (
    BaseDocTemplate, PageTemplate, Frame, Paragraph, 
    Spacer, KeepTogether, Table, TableStyle, HRFlowable, PageBreak
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY

# --- 1. FUNÇÃO DO DESIGN DO PDF ---
def desenhar_divisoria_central(canvas, doc):
    canvas.saveState()
    centro_x = 612 / 2
    topo_y = 792 - 54     
    fim_y = 54            
    canvas.setStrokeColor(colors.HexColor('#CBD5E0'))
    canvas.setLineWidth(0.5)
    canvas.line(centro_x, topo_y, centro_x, fim_y)
    canvas.restoreState()

def gerar_pdf_stream(dados):
    pdf_buffer = io.BytesIO()
    largura_pag, altura_pag = letter
    margem = 40 
    largura_util = largura_pag - (2 * margem) 
    espaco_entre_colunas = 20
    largura_coluna = (largura_util - espaco_entre_colunas) / 2 
    altura_util = altura_pag - (2 * margem) 

    frame_esquerda = Frame(margem, margem, largura_coluna, altura_util, id='col1', leftPadding=0, rightPadding=10, topPadding=0, bottomPadding=0)
    frame_direita = Frame(margem + largura_coluna + espaco_entre_colunas, margem, largura_coluna, altura_util, id='col2', leftPadding=10, rightPadding=0, topPadding=0, bottomPadding=0)

    doc = BaseDocTemplate(pdf_buffer, pagesize=letter)
    template = PageTemplate(id='DuasColunas', frames=[frame_esquerda, frame_direita], onPage=desenhar_divisoria_central)
    doc.addPageTemplates([template])
    
    styles = getSampleStyleSheet()
    style_materia = ParagraphStyle('Mat', parent=styles['Heading1'], fontName='Helvetica-Bold', fontSize=18, leading=22, textColor=colors.HexColor('#1A365D'), alignment=TA_CENTER, spaceAfter=10)
    style_tema = ParagraphStyle('Tem', parent=styles['Heading2'], fontName='Helvetica-Bold', fontSize=12, leading=15, textColor=colors.HexColor('#2B6CB0'), spaceBefore=10, spaceAfter=8)
    style_enunciado = ParagraphStyle('Enun', parent=styles['Normal'], fontName='Helvetica', fontSize=10, leading=14, textColor=colors.HexColor('#2D3748'), alignment=TA_JUSTIFY, spaceAfter=4)
    style_assertiva = ParagraphStyle('Ass', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=10, leading=14, textColor=colors.black, alignment=TA_JUSTIFY)
    style_gabarito_titulo = ParagraphStyle('GabTit', parent=styles['Heading2'], fontName='Helvetica-Bold', fontSize=14, leading=18, textColor=colors.HexColor('#1A365D'), spaceBefore=15, spaceAfter=10, alignment=TA_CENTER)

    story = []
    story.append(Paragraph(dados['Materia'].upper(), style_materia))
    story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor('#1A365D'), spaceAfter=15))
    
    lista_gabaritos = []
    lista_comentarios = []
    
    for tema in dados['Temas']:
        story.append(Paragraph(f"TEMA: {tema['NomeTema']}", style_tema))
        story.append(Spacer(1, 5))
        
        for q in tema['Questoes']:
            num_q = q['Id']
            gabarito = q['Gabarito'].upper()
            lista_gabaritos.append((num_q, gabarito))
            lista_comentarios.append((num_q, gabarito, q['Comentario']))
            
            bloco_questao = []
            bloco_questao.append(Paragraph(f"<b>{num_q}.</b> {q['Enunciado']}", style_enunciado))
            opcao_texto = f"<b>( &nbsp;C&nbsp; ) &nbsp; ( &nbsp;E&nbsp; )</b>"
            bloco_questao.append(Paragraph(opcao_texto, style_assertiva))
            bloco_questao.append(Spacer(1, 15))
            story.append(KeepTogether(bloco_questao))
            
    story.append(PageBreak())
    story.append(Paragraph("GABARITO OFICIAL", style_gabarito_titulo))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#CBD5E0'), spaceBefore=5, spaceAfter=15))
    
    dados_tabela = []
    linha_atual = []
    for num, gab in lista_gabaritos:
        linha_atual.append(Paragraph(f"<b>{num}:</b> &nbsp;{gab}", style_enunciado))
        if len(linha_atual) == 4:
            dados_tabela.append(linha_atual)
            linha_atual = []
    if linha_atual:
        while len(linha_atual) < 4:
            linha_atual.append(Paragraph("", style_enunciado))
        dados_tabela.append(linha_atual)
        
    tabela_gab = Table(dados_tabela, colWidths=[60]*4)
    tabela_gab.setStyle(TableStyle([
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#E2E8F0')),
        ('TOPPADDING', (0,0), (-1,-1), 5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 5),
    ]))
    story.append(tabela_gab)
    story.append(Spacer(1, 20))
    
    story.append(Paragraph("GABARITO COMENTADO", style_gabarito_titulo))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#CBD5E0'), spaceBefore=5, spaceAfter=15))
    
    for num, gab, comentario in lista_comentarios:
        bloco_comentario = []
        bloco_comentario.append(Paragraph(f"<b>Questão {num} — Gabarito: {gab}</b>", style_assertiva))
        bloco_comentario.append(Paragraph(f"<b>Justificativa:</b> {comentario}", style_enunciado))
        bloco_comentario.append(HRFlowable(width="100%", thickness=0.3, color=colors.HexColor('#E2E8F0'), spaceBefore=5, spaceAfter=10))
        story.append(KeepTogether(bloco_comentario))

    doc.build(story)
    pdf_buffer.seek(0)
    return pdf_buffer

# --- 2. CONFIGURAÇÃO DA INTERFACE DA APLICAÇÃO ---
st.set_page_config(page_title="Gerador Pipoco", page_icon="⚡", layout="centered")

# Injeção de CSS Blindado contra Dark Mode
st.markdown("""
    <style>
    body {
        background-color: #F7FAFC;
    }
    
    h1 {
        color: #1A365D !important;
        font-family: 'Arial Black', sans-serif;
        text-shadow: 2px 2px 0px #845ec2;
    }
    
    /* Força o título e textos explicativos a ficarem escuros e visíveis */
    .stMarkdown p {
        color: #2D3748 !important;
    }
    
    /* Customização da Caixa de Texto (Fundo creme e texto PRETO obrigatório) */
    .stTextArea textarea {
        color: #000000 !important;
        background-color: #FFFDF5 !important;
        border: 3px solid #1A365D !important;
        border-radius: 12px !important;
        font-family: 'Courier New', Courier, monospace !important;
        font-size: 15px !important;
    }
    
    /* Garante que o texto digitado continue preto mesmo sob foco/seleção */
    .stTextArea textarea:focus {
        color: #000000 !important;
        background-color: #FFFDF5 !important;
        border-color: #2B6CB0 !important;
    }
    
    /* Botão Amarelo de Enviar */
    .stButton button {
        background-color: #FFD43B !important;
        color: #1A365D !important;
        font-weight: bold !important;
        font-size: 16px !important;
        border: 3px solid #1A365D !important;
        border-radius: 12px !important;
        box-shadow: 3px 3px 0px #1A365D !important;
    }
    
    /* Botão Verde de Download */
    .stDownloadButton button {
        background-color: #48BB78 !important;
        color: white !important;
        font-weight: bold !important;
        font-size: 18px !important;
        border: 3px solid #1A365D !important;
        border-radius: 15px !important;
        box-shadow: 4px 4px 0px #1A365D !important;
    }
    </style>
""", unsafe_allow_html=True)

st.title("⚡ Gerador de Simulados")
st.write("Insira o código gerado no campo de texto e clique no botão para obter seu PDF.")

# Formulário estável
with st.form(key="formulario_json"):
    json_input = st.text_area(
        "Cole o conteúdo do JSON aqui:", 
        height=300, 
        placeholder="Cole o código JSON completo aqui..."
    )
    botao_enviar = st.form_submit_button(label="🚀 PROCESSAR QUESTÕES", use_container_width=True)

if botao_enviar:
    if not json_input.strip():
        st.warning("⚠️ Ei, a caixa está vazia! Cole o conteúdo antes de enviar.")
    else:
        try:
            dados_validados = json.loads(json_input)
            st.session_state['dados_pdf'] = dados_validados
            st.toast("✨ Tudo certo! Seu caderno foi estruturado com sucesso.", icon="🎉")
        except json.JSONDecodeError as e:
            st.error(f"❌ Conteúdo inválido. Certifique-se de copiar o JSON completo. Erro: {e}")

if 'dados_pdf' in st.session_state:
    st.markdown("<br>", unsafe_allow_html=True)
    pdf_data = gerar_pdf_stream(st.session_state['dados_pdf'])
    st.download_button(
        label="📥 BAIXAR CADERNO FORMATADO (.PDF)",
        data=pdf_data,
        file_name="Simulado_Final.pdf",
        mime="application/pdf",
        use_container_width=True
    )