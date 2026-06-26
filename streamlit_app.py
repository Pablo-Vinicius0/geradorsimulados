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

# --- 1. DESIGN DO BACKGROUND DO PDF (DUAS COLUNAS) ---
def desenhar_divisoria_central(canvas, doc):
    canvas.saveState()
    centro_x = 612 / 2
    topo_y = 792 - 54     
    fim_y = 54            
    canvas.setStrokeColor(colors.HexColor('#E2E8F0'))  
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
    
    style_materia = ParagraphStyle('Mat', parent=styles['Heading1'], fontName='Helvetica-Bold', fontSize=18, leading=22, textColor=colors.HexColor('#0F172A'), alignment=TA_CENTER, spaceAfter=2)
    style_submateria = ParagraphStyle('SubMat', parent=styles['Normal'], fontName='Helvetica', fontSize=11, leading=14, textColor=colors.HexColor('#475569'), alignment=TA_CENTER, spaceAfter=8)
    style_banca_tag = ParagraphStyle('BancaTag', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=9, leading=12, textColor=colors.HexColor('#2563EB'), alignment=TA_CENTER, spaceAfter=12)
    
    style_tema = ParagraphStyle('Tem', parent=styles['Heading2'], fontName='Helvetica-Bold', fontSize=12, leading=15, textColor=colors.HexColor('#1E293B'), spaceBefore=10, spaceAfter=8)
    style_enunciado = ParagraphStyle('Enun', parent=styles['Normal'], fontName='Helvetica', fontSize=10, leading=14, textColor=colors.HexColor('#334155'), alignment=TA_JUSTIFY, spaceAfter=4)
    style_seletor = ParagraphStyle('Sel', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=10, leading=14, textColor=colors.black, alignment=TA_JUSTIFY)
    style_opcao_multipla = ParagraphStyle('OpMed', parent=styles['Normal'], fontName='Helvetica', fontSize=9.5, leading=13, textColor=colors.black, alignment=TA_JUSTIFY, spaceAfter=2)
    
    style_gabarito_titulo = ParagraphStyle('GabTit', parent=styles['Heading2'], fontName='Helvetica-Bold', fontSize=14, leading=18, textColor=colors.HexColor('#0F172A'), spaceBefore=15, spaceAfter=10, alignment=TA_CENTER)
    style_coment_texto = ParagraphStyle('ComTex', parent=styles['Normal'], fontName='Helvetica', fontSize=9.5, leading=13.5, textColor=colors.HexColor('#334155'), alignment=TA_JUSTIFY, spaceAfter=4)

    story = []
    
    story.append(Paragraph(dados['Materia'].upper(), style_materia))
    if 'Submateria' in dados:
        story.append(Paragraph(dados['Submateria'], style_submateria))
    if 'Banca' in dados:
        story.append(Paragraph(f"BANCA COMPILADA: {dados['Banca'].upper()}", style_banca_tag))
        
    story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor('#0F172A'), spaceAfter=15))
    
    lista_gabaritos = []
    lista_comentarios = []
    total_questoes = 0
    
    # Navegação corrigida: Coleta as questões dentro do nó de "Temas" de forma linear
    temas = dados.get('Temas', [])
    if not temas and 'Estrutura' in dados:
        temas = dados.get('Estrutura', {}).get('Temas', [])
        
    for tema in temas:
        story.append(Paragraph(f"TEMA: {tema['NomeTema']}", style_tema))
        story.append(Spacer(1, 5))
        
        for q in tema.get('Questoes', []):
            total_questoes += 1
            num_q = q['Id']
            gabarito = q['Gabarito'].upper()
            lista_gabaritos.append((num_q, gabarito))
            
            analise = q.get('AnaliseDetalhada', q)
            lista_comentarios.append({
                'id': num_q,
                'gabarito': gabarito,
                'comentario': analise.get('Comentario', ''),
                'pegadinha': analise.get('Pegadinha', ''),
                'dica': analise.get('DicaMemorizacao', '')
            })
            
            bloco_questao = []
            bloco_questao.append(Paragraph(f"<b>{num_q}.</b> {q['Enunciado']}", style_enunciado))
            
            if tipo_questao == "Certo / Errado":
                opcao_texto = f"<b>( &nbsp;C&nbsp; ) &nbsp; ( &nbsp;E&nbsp; )</b>"
                bloco_questao.append(Paragraph(opcao_texto, style_seletor))
            else:
                if "Opcoes" in q:
                    for opt in q["Opcoes"]:
                        bloco_questao.append(Paragraph(opt, style_opcao_multipla))
                else:
                    for letra in ['A', 'B', 'C', 'D', 'E']:
                        bloco_questao.append(Paragraph(f"<b>{letra})</b> ___________________________", style_opcao_multipla))
            
            bloco_questao.append(Spacer(1, 15))
            story.append(KeepTogether(bloco_questao))
            
    # Captura métricas e resumos caso estejam envelopados em estruturas complexas
    estrutura_base = dados.get('Estrutura', dados)
    metricas = estrutura_base.get('MetricasBanca', {})
    if metricas:
        bloco_metricas = [PageBreak() if total_questoes > 4 else Spacer(1, 10)]
        bloco_metricas.append(Paragraph("MÉTRICAS DA BANCA", style_gabarito_titulo))
        bloco_metricas.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#E2E8F0'), spaceAfter=10))
        
        if "DezErrosMaisComuns" in metricas:
            bloco_metricas.append(Paragraph("<b>Erros Mais Comuns dos Candidatos:</b>", style_tema))
            for erro in metricas["DezErrosMaisComuns"]:
                bloco_metricas.append(Paragraph(f"• {erro}", style_enunciado))
                bloco_metricas.append(Spacer(1, 2))
                
        if "AssuntosMaisRecorrentes" in metricas:
            bloco_metricas.append(Spacer(1, 8))
            bloco_metricas.append(Paragraph("<b>Assuntos Mais Recorrentes:</b>", style_tema))
            for assunto in metricas["AssuntosMaisRecorrentes"]:
                bloco_metricas.append(Paragraph(f"✔ {assunto}", style_enunciado))
                bloco_metricas.append(Spacer(1, 2))
        
        story.append(KeepTogether(bloco_metricas))

    resumo = estrutura_base.get('ResumoVespera', {})
    if resumo:
        bloco_resumo = []
        if not metricas:
            bloco_resumo.append(PageBreak())
        else:
            bloco_resumo.append(Spacer(1, 15))
            
        bloco_resumo.append(Paragraph("RESUMO DE VÉSPERA", style_gabarito_titulo))
        bloco_resumo.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#E2E8F0'), spaceAfter=10))
        
        if "MecanismoCifrão" in resumo:
            bloco_resumo.append(Paragraph(f"<b>Mecanismo do Cifrão ($):</b> {resumo['MecanismoCifrão']}", style_enunciado))
            bloco_resumo.append(Spacer(1, 6))
            
        if "SintaxeOperadores" in resumo:
            bloco_resumo.append(Paragraph("<b>Sintaxe e Operadores Chave:</b>", style_tema))
            for k, v in resumo["SintaxeOperadores"].items():
                bloco_resumo.append(Paragraph(f"• <b>{k}:</b> {v}", style_enunciado))
                
        if "CodigosErro" in resumo:
            bloco_resumo.append(Spacer(1, 6))
            bloco_resumo.append(Paragraph("<b>Códigos de Erro Comuns:</b>", style_tema))
            for k, v in resumo["CodigosErro"].items():
                bloco_resumo.append(Paragraph(f"• <b>#{k}:</b> {v}", style_enunciado))
                
        if "AtalhosChave" in resumo:
            bloco_resumo.append(Spacer(1, 6))
            bloco_resumo.append(Paragraph("<b>Teclas de Atalho Essenciais:</b>", style_tema))
            for k, v in resumo["AtalhosChave"].items():
                bloco_resumo.append(Paragraph(f"• <b>{k}:</b> {v}", style_enunciado))
                
        story.append(KeepTogether(bloco_resumo))

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
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#CBD5E0')),
        ('TOPPADDING', (0,0), (-1,-1), 5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 5),
    ]))
    story.append(tabela_gab)
    story.append(Spacer(1, 25))
    
    story.append(Paragraph("GABARITO COMENTADO", style_gabarito_titulo))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#E2E8F0'), spaceBefore=5, spaceAfter=15))
    
    for item in lista_comentarios:
        bloco_comentario = []
        bloco_comentario.append(Paragraph(f"<b>Questão {item['id']} — Gabarito Oficial: {item['gabarito']}</b>", style_seletor))
        bloco_comentario.append(Paragraph(f"<b>Análise:</b> {item['comentario']}", style_coment_texto))
        
        if item['pegadinha']:
            bloco_comentario.append(Paragraph(f"<b>⚠️ Cuidado com a Pegadinha:</b> {item['pegadinha']}", style_coment_texto))
        if item['dica']:
            bloco_comentario.append(Paragraph(f"<b>💡 Dica de Memorização:</b> {item['dica']}", style_coment_texto))
            
        bloco_comentario.append(HRFlowable(width="100%", thickness=0.3, color=colors.HexColor('#E2E8F0'), spaceBefore=6, spaceAfter=12))
        story.append(KeepTogether(bloco_comentario))

    doc.build(story)
    pdf_buffer.seek(0)
    return pdf_buffer

# --- 2. CONFIGURAÇÃO DA INTERFACE STREAMLIT ---
st.set_page_config(page_title="Compilador Minimalista", page_icon="📄", layout="centered")

st.markdown("""
    <style>
    .stApp { background-color: #F8FAFC !important; }
    h2 { color: #0F172A !important; font-family: -apple-system, BlinkMacSystemFont, sans-serif; font-weight: 700 !important; }
    .stMarkdown p, label, span, .stWidgetLabel p { color: #1E293B !important; font-weight: 600 !important; opacity: 1 !important; }
    div[data-testid="stForm"] { background-color: #FFFFFF !important; border: 2px solid #E2E8F0 !important; border-radius: 12px !important; padding: 24px !important; }
    .stTextArea textarea, .stSelectbox div[data-baseweb="select"], .stTextInput input { color: #000000 !important; background-color: #FFFFFF !important; border: 2px solid #CBD5E1 !important; border-radius: 6px !important; }
    input, textarea, select { color: #000000 !important; }
    .stButton button { background-color: #0F172A !important; color: #FFFFFF !important; font-weight: 600 !important; border: 2px solid #0F172A !important; border-radius: 6px !important; padding: 10px 20px !important; }
    .stButton button:hover { background-color: #1E293B !important; border-color: #1E293B !important; }
    .stDownloadButton button { background-color: #059669 !important; color: #FFFFFF !important; font-weight: 600 !important; border: 2px solid #059669 !important; border-radius: 6px !important; }
    .stDownloadButton button:hover { background-color: #047857 !important; border-color: #047857 !important; }
    </style>
""", unsafe_allow_html=True)

st.write("<h2>Compilador de Simulados Avançado</h2>", unsafe_allow_html=True)

with st.form(key="formulario_minimalista"):
    tipo_selecionado = st.selectbox("Formato das questões:", ["Certo / Errado", "Múltipla Escolha (A até E)"])
    nome_arquivo_input = st.text_input("Nome do arquivo PDF (Opcional):", placeholder="Ex: Simulado_Constitucional")
    json_input = st.text_area("Código estruturado (JSON):", height=300, placeholder="Cole a estrutura JSON aqui...")
    botao_enviar = st.form_submit_button(label="Processar e Estruturar", use_container_width=True)

if botao_enviar:
    if not json_input.strip():
        st.warning("Por favor, insira o conteúdo antes de submeter.")
    else:
        try:
            dados_validados = json.loads(json_input)
            st.session_state['dados_pdf'] = dados_validados
            st.session_state['tipo_pdf'] = tipo_selecionado
            
            if nome_arquivo_input.strip():
                nome_limpo = nome_arquivo_input.strip().replace(".pdf", "").replace(".PDF", "")
                nome_final = f"{nome_limpo}.pdf"
            else:
                nome_seguro = dados_validados.get('Materia', 'Simulado').replace(" ", "_").replace("/", "_")
                nome_final = f"{nome_seguro}.pdf"
                
            st.session_state['nome_arquivo_pdf'] = nome_final
            st.toast("Dados validados com sucesso.", icon="✅")
            
        except json.JSONDecodeError as e:
            st.error(f"Erro na leitura dos dados. Verifique o JSON. Detalhes: {e}")

if 'dados_pdf' in st.session_state:
    st.markdown("<br>", unsafe_allow_html=True)
    pdf_data = gerar_pdf_stream(st.session_state['dados_pdf'], st.session_state['tipo_pdf'])
    st.download_button(
        label="📥 Baixar Caderno Formatado",
        data=pdf_data,
        file_name=st.session_state['nome_arquivo_pdf'],
        mime="application/pdf",
        use_container_width=True
    )
