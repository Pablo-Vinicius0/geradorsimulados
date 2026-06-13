import json
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

# --- 1. FUNÇÃO DO DESIGN DO PDF (DUAS COLUNAS COM DIVISÓRIA) ---
def desenhar_divisoria_central(canvas, doc):
    canvas.saveState()
    centro_x = 612 / 2
    topo_y = 792 - 54     
    fim_y = 54            
    canvas.setStrokeColor(colors.HexColor('#E2E8F0'))  # Cinza bem sutil
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
    style_materia = ParagraphStyle('Mat', parent=styles['Heading1'], fontName='Helvetica-Bold', fontSize=18, leading=22, textColor=colors.HexColor('#0F172A'), alignment=TA_CENTER, spaceAfter=10)
    style_tema = ParagraphStyle('Tem', parent=styles['Heading2'], fontName='Helvetica-Bold', fontSize=12, leading=15, textColor=colors.HexColor('#334155'), spaceBefore=10, spaceAfter=8)
    style_enunciado = ParagraphStyle('Enun', parent=styles['Normal'], fontName='Helvetica', fontSize=10, leading=14, textColor=colors.HexColor('#334155'), alignment=TA_JUSTIFY, spaceAfter=4)
    style_assertiva = ParagraphStyle('Ass', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=10, leading=14, textColor=colors.black, alignment=TA_JUSTIFY)
    style_opcao_multipla = ParagraphStyle('OpMed', parent=styles['Normal'], fontName='Helvetica', fontSize=9.5, leading=13, textColor=colors.black, alignment=TA_JUSTIFY, spaceAfter=2)
    style_gabarito_titulo = ParagraphStyle('GabTit', parent=styles['Heading2'], fontName='Helvetica-Bold', fontSize=14, leading=18, textColor=colors.HexColor('#0F172A'), spaceBefore=15, spaceAfter=10, alignment=TA_CENTER)

    story = []
    story.append(Paragraph(dados['Materia'].upper(), style_materia))
    story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor('#0F172A'), spaceAfter=15))
    
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
            
            if tipo_questao == "Certo / Errado":
                opcao_texto = f"<b>( &nbsp;C&nbsp; ) &nbsp; ( &nbsp;E&nbsp; )</b>"
                bloco_questao.append(Paragraph(opcao_texto, style_assertiva))
            else:
                if "Opcoes" in q:
                    for opt in q["Opcoes"]:
                        bloco_questao.append(Paragraph(opt, style_opcao_multipla))
                else:
                    for letra in ['A', 'B', 'C', 'D', 'E']:
                        bloco_questao.append(Paragraph(f"<b>{letra})</b> ___________________________", style_opcao_multipla))
            
            bloco_questao.append(Spacer(1, 15))
            story.append(KeepTogether(bloco_questao))
            
    story.append(PageBreak())
    story.append(Paragraph("GABARITO OFICIAL", style_gabarito_titulo))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#E2E8F0'), spaceBefore=5, spaceAfter=15))
    
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
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#E2E8F0'), spaceBefore=5, spaceAfter=15))
    
    for num, gab, comentario in lista_comentarios:
        bloco_comentario = []
        bloco_comentario.append(Paragraph(f"<b>Questão {num} — Gabarito: {gab}</b>", style_assertiva))
        bloco_comentario.append(Paragraph(f"<b>Justificativa:</b> {comentario}", style_enunciado))
        bloco_comentario.append(HRFlowable(width="100%", thickness=0.3, color=colors.HexColor('#E2E8F0'), spaceBefore=5, spaceAfter=10))
        story.append(KeepTogether(bloco_comentario))

    doc.build(story)
    pdf_buffer.seek(0)
    return pdf_buffer

# --- 2. CONFIGURAÇÃO DA INTERFACE (ESTILO COMPATÍVEL ESCOPO MINIMALISTA) ---
st.set_page_config(page_title="Compilador Minimalista", page_icon="📄", layout="centered")

# CSS para o visual Moderno, Limpo e Minimalista (Sem bordas gritantes ou gradientes excessivos)
st.markdown("""
    <style>
    /* Fundo suave e neutro */
    .stApp {
        background-color: #FAFAFA !important;
    }
    
    /* Título elegante */
    h2 {
        color: #0F172A !important;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
        font-weight: 600;
        letter-spacing: -0.5px;
    }
    
    /* Container do formulário clean, como um card moderno */
    div[data-testid="stForm"] {
        background-color: #FFFFFF !important;
        border: 1px solid #E4E4E7 !important;
        border-radius: 12px !important;
        box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.05), 0 1px 2px 0 rgba(0, 0, 0, 0.03) !important;
        padding: 24px !important;
    }
    
    /* Textos secundários */
    .stMarkdown p, label {
        color: #4B5563 !important;
        font-family: -apple-system, BlinkMacSystemFont, sans-serif;
    }
    
    /* Inputs arredondados e discretos */
    .stTextArea textarea, .stSelectbox div[data-baseweb="select"], .stTextInput input {
        color: #0F172A !important;
        background-color: #FFFFFF !important;
        border: 1px solid #E4E4E7 !important;
        border-radius: 6px !important;
        font-size: 14px !important;
    }
    
    /* Foco nos Inputs */
    .stTextArea textarea:focus, .stTextInput input:focus {
        border-color: #0F172A !important;
        box-shadow: 0 0 0 1px #0F172A !important;
    }
    
    /* Botão de Ação Primária Minimalista (Preto / Slate Escuro) */
    .stButton button {
        background-color: #0F172A !important;
        color: #FFFFFF !important;
        font-weight: 500 !important;
        font-size: 14px !important;
        border: 1px solid #0F172A !important;
        border-radius: 6px !important;
        transition: background-color 0.15s ease;
        padding: 8px 16px !important;
    }
    
    .stButton button:hover {
        background-color: #1E293B !important;
        color: #FFFFFF !important;
        border-color: #1E293B !important;
    }
    
    /* Botão de Download com tom neutro de sucesso */
    .stDownloadButton button {
        background-color: #059669 !important;
        color: #FFFFFF !important;
        font-weight: 500 !important;
        font-size: 15px !important;
        border: 1px solid #059669 !important;
        border-radius: 6px !important;
        margin-top: 15px;
    }
    
    .stDownloadButton button:hover {
        background-color: #047857 !important;
        color: #FFFFFF !important;
        border-color: #047857 !important;
    }
    </style>
""", unsafe_allow_html=True)

st.write("<h2>Compilador de Simulados</h2>", unsafe_allow_html=True)
st.write("Converta estruturas de dados em cadernos de prova diagramados de forma simples.")

# Formulário único e limpo
with st.form(key="formulario_minimalista"):
    
    # 1. Menu de seleção do Tipo de Questão
    tipo_selecionado = st.selectbox(
        "Formato das questões:",
        ["Múltipla Escolha (A até E)", "Certo / Errado"]
    )
    
    # 2. Campo opcional para nomear o arquivo final
    nome_arquivo_input = st.text_input(
        "Nome do arquivo PDF (Opcional):",
        placeholder="Ex: Simulado_Constitucional_Fcc (Não precisa digitar .pdf)"
    )
    
    # 3. Área de Texto para o JSON
    json_input = st.text_area(
        "Código estruturado (JSON):", 
        height=280, 
        placeholder="{\n  \"Materia\": \"Nome da Disciplina\",\n  \"Temas\": [...]\n}"
    )
    
    # Botão de envio
    botao_enviar = st.form_submit_button(label="Processar e Estruturar", use_container_width=True)

# Lógica de validação pós-clique
if botao_enviar:
    if not json_input.strip():
        st.warning("Por favor, insira o conteúdo antes de submeter.")
    else:
        try:
            dados_validados = json.loads(json_input)
            st.session_state['dados_pdf'] = dados_validados
            st.session_state['tipo_pdf'] = tipo_selecionado
            
            # Define o nome do arquivo final
            if nome_arquivo_input.strip():
                # Remove o .pdf caso o usuário tenha digitado manualmente
                nome_limpo = nome_arquivo_input.strip().replace(".pdf", "").replace(".PDF", "")
                nome_final = f"{nome_limpo}.pdf"
            else:
                # Fallback: Usa o nome da matéria presente no JSON (substituindo espaços por underlines)
                nome_seguro = dados_validados.get('Materia', 'Simulado').replace(" ", "_")
                nome_final = f"{nome_seguro}.pdf"
                
            st.session_state['nome_arquivo_pdf'] = nome_final
            st.toast("Dados validados com sucesso.", icon="✓")
            
        except json.JSONDecodeError as e:
            st.error(f"Erro na leitura dos dados. Verifique a formatação do código. Detalhes: {e}")

# Renderização do botão de download fora do formulário para evitar reloads
if 'dados_pdf' in st.session_state:
    pdf_data = gerar_pdf_stream(st.session_state['dados_pdf'], st.session_state['tipo_pdf'])
    
    st.download_button(
        label=f"📥 Baixar Arquivo ({st.session_state['nome_arquivo_pdf']})",
        data=pdf_data,
        file_name=st.session_state['nome_arquivo_pdf'],
        mime="application/pdf",
        use_container_width=True
    )
