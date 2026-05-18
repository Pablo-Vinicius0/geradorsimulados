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

def gerar_pdf_stream(dados, tipo_questao):
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
    style_opcao_multipla = ParagraphStyle('OpMed', parent=styles['Normal'], fontName='Helvetica', fontSize=9.5, leading=13, textColor=colors.black, alignment=TA_JUSTIFY, spaceAfter=2)
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
            
            # Condicional de renderização baseado no tipo selecionado na UI
            if tipo_questao == "Certo / Errado":
                opcao_texto = f"<b>( &nbsp;C&nbsp; ) &nbsp; ( &nbsp;E&nbsp; )</b>"
                bloco_questao.append(Paragraph(opcao_texto, style_assertiva))
            else:
                # Múltipla Escolha: Varre e renderiza as alternativas do JSON
                if "Opcoes" in q:
                    for opt in q["Opcoes"]:
                        bloco_questao.append(Paragraph(opt, style_opcao_multipla))
                else:
                    # Fallback visual caso falte o nó no JSON
                    for letra in ['A', 'B', 'C', 'D', 'E']:
                        bloco_questao.append(Paragraph(f"<b>{letra})</b> ___________________________", style_opcao_multipla))
            
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

# --- 2. CONFIGURAÇÃO DA INTERFACE DA APLICAÇÃO (TEMA WINDOWS 7 AERO) ---
st.set_page_config(page_title="Windows 7 Simulators", page_icon="💻", layout="centered")

st.markdown("""
    <style>
    /* Fundo clássico texturizado do Windows 7 */
    .stApp {
        background: linear-gradient(135deg, #3a7bd5, #3a6073) !important;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif !important;
    }
    
    /* Janela Principal Estilo Windows Aero Glass */
    div[data-testid="stForm"] {
        background: rgba(235, 245, 255, 0.85) !important;
        border: 1px solid rgba(255, 255, 255, 0.4) !important;
        border-radius: 8px !important;
        box-shadow: 0 10px 30px rgba(0,0,0,0.3), inset 0 1px 0 rgba(255,255,255,0.6) !important;
        padding: 0px !important; /* Controlado pelo header interno */
        overflow: hidden;
    }
    
    /* Barra de Título Azul do Windows 7 */
    .win7-header {
        background: linear-gradient(to bottom, #7abcff 0%, #60abf8 44%, #4096ee 100%);
        padding: 10px 15px;
        color: #ffffff;
        font-weight: bold;
        font-size: 16px;
        text-shadow: 1px 1px 2px rgba(0,0,0,0.5);
        border-bottom: 1px solid #2d70b5;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }
    
    .win7-body {
        padding: 20px;
    }
    
    /* Textos da UI */
    .stMarkdown p, label {
        color: #1e395b !important;
        font-weight: 500 !important;
    }
    
    /* Customização dos Inputs (Caixa de Texto e Selectbox) */
    .stTextArea textarea, .stSelectbox div[data-baseweb="select"] {
        color: #000000 !important;
        background-color: #ffffff !important;
        border: 1px solid #7f9db9 !important;
        border-radius: 3px !important;
        box-shadow: inset 1px 1px 2px rgba(0,0,0,0.1) !important;
    }
    
    /* Botões Clássicos com Efeito Gel/Gradiente do Windows 7 */
    .stButton button, .stDownloadButton button {
        background: linear-gradient(to bottom, #f2f2f2 0%, #ebebeb 50%, #dddddd 51%, #cfcfcf 100%) !important;
        color: #333333 !important;
        font-family: 'Segoe UI', sans-serif !important;
        font-size: 14px !important;
        border: 1px solid #707070 !important;
        border-radius: 3px !important;
        box-shadow: inset 0 1px 0 #ffffff, 1px 1px 2px rgba(0,0,0,0.1) !important;
        text-shadow: 0 1px 0 #ffffff;
        transition: all 0.1s ease;
    }
    
    /* Efeito de Hover nos botões (Brilho azul suave) */
    .stButton button:hover, .stDownloadButton button:hover {
        border-color: #3c7fb1 !important;
        background: linear-gradient(to bottom, #eaf6fd 0%, #d9f0fc 50%, #bee6fd 51%, #a7d9f5 100%) !important;
        box-shadow: 0 0 5px #a7d9f5 !important;
    }
    
    /* Botão de Download em Destaque */
    .stDownloadButton button {
        background: linear-gradient(to bottom, #eaf6fd 0%, #bee6fd 50%, #a7d9f5 51%, #79bde8 100%) !important;
        border-color: #3c7fb1 !important;
        margin-top: 10px;
    }
    </style>
""", unsafe_allow_html=True)

# Título fora da janela simulada
st.write("<h2 style='color:white; text-shadow: 1px 1px 4px rgba(0,0,0,0.6); font-family:Sans-Serif;'>💻 Gerador de Simulados 2006</h2>", unsafe_allow_html=True)

# Início da Janela estruturada do Windows 7
with st.form(key="formulario_windows7"):
    # Renderiza a barra superior nativa do sistema operacional antigo
    st.markdown("""
        <div class="win7-header">
            <span>Conversor de Simulados (.JSON &rarr; .PDF)</span>
            <span style="font-size: 12px; letter-spacing: 2px;">🗕 🗖 🗙</span>
        </div>
    """, unsafe_allow_html=True)
    
    # Div para aplicar o espaçamento correto interno
    st.markdown('<div class="win7-body">', unsafe_allow_html=True)
    
    # 1. Menu de seleção do Tipo de Questão
    tipo_selecionado = st.selectbox(
        "Selecione o modelo do caderno de provas:",
        ["Certo / Errado", "Múltipla Escolha (A até E)"]
    )
    
    # 2. Área de Texto para colar o JSON
    json_input = st.text_area(
        "Cole o código gerado abaixo:", 
        height=250, 
        placeholder="{\n  \"Materia\": \"...\"\n}"
    )
    
    # 3. Botão de Envio do Formulário Windows
    botao_enviar = st.form_submit_button(label="Aplicar e Compilar", use_container_width=True)
    
    st.markdown('</div>', unsafe_allow_html=True)

# Processamento lógico
if botao_enviar:
    if not json_input.strip():
        st.warning("Atenção: A área de transferência de dados está vazia.")
    else:
        try:
            dados_validados = json.loads(json_input)
            # Guarda também o tipo escolhido na sessão
            st.session_state['dados_pdf'] = dados_validados
            st.session_state['tipo_pdf'] = tipo_selecionado
            st.toast("Operação concluída com sucesso no sistema.", icon="ℹ️")
        except json.JSONDecodeError as e:
            st.error(f"Erro de Sintaxe no Arquivo. Certifique-se de fechar todas as chaves. Log: {e}")

# Janela de Download posterior
if 'dados_pdf' in st.session_state:
    pdf_data = gerar_pdf_stream(st.session_state['dados_pdf'], st.session_state['tipo_pdf'])
    st.download_button(
        label="💾 Gravar Arquivo PDF no Disco",
        data=pdf_data,
        file_name="Simulado_Gerado.pdf",
        mime="application/pdf",
        use_container_width=True
    )