import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
import re
import json
import os
import threading
from xmlforge import layout_parser as parser
from xmlforge.temas import GerenciadorTemas
from xmlforge.utils import processar_template_com_dominios
from xmlforge import config_manager
try:
    import pymqi
    PYMQI_DISPONIVEL = True
except ImportError:
    PYMQI_DISPONIVEL = False
    print("AVISO: pymqi não está instalado. Funcionalidade de envio para fila MQ desabilitada.")

# Inicializa o gerenciador de temas
gerenciador_temas = GerenciadorTemas()

# Função global para atualizar números de linha (será definida no main)
atualizar_numeros_linha_func = None

# Variáveis globais para gerenciamento de conexão MQ
qmgr_connection = None
queue_connection = None
ambiente_atual = None

def gerar_saida():
    tag = tag_var.get()
    if not tag:
        return
    
    # Recarrega os domínios para pegar atualizações do arquivo
    parser.carregar_json()
    
    # Debug: mostra quantos domínios foram carregados
    print(f"DEBUG: {len(parser.DOMINIOS)} domínios carregados")
    if parser.DOMINIOS:
        print(f"DEBUG: Primeiras 5 tags com domínio: {list(parser.DOMINIOS.keys())[:5]}")
    
    campo_resultado.delete(1.0, tk.END)
    xml = parser.extrair_tags(tag)
    
    # Adiciona cabeçalho e rodapé baseado no sufixo da mensagem
    if tag.endswith('R1') and 'R1' in parser.TEMPLATES:
        template = parser.TEMPLATES['R1']
        header = template.get('header', '')
        footer = template.get('footer', '')
        # Processa header e footer para adicionar marcadores de domínio
        header = processar_template_com_dominios(header, parser.DOMINIOS)
        footer = processar_template_com_dominios(footer, parser.DOMINIOS)
        # Indenta o corpo do XML com dois tabs extras (dentro de <MsgXML>)
        xml_indentado = '\n'.join(['\t\t' + linha if linha.strip() else linha for linha in xml.split('\n')])
        xml = header + '\n' + xml_indentado + '\n' + footer
    elif tag.endswith('R2') and 'R2' in parser.TEMPLATES:
        template = parser.TEMPLATES['R2']
        header = template.get('header', '')
        footer = template.get('footer', '')
        # Processa header e footer para adicionar marcadores de domínio
        header = processar_template_com_dominios(header, parser.DOMINIOS)
        footer = processar_template_com_dominios(footer, parser.DOMINIOS)
        # Indenta o corpo do XML com três tabs extras (dentro de <SISMSG>)
        xml_indentado = '\n'.join(['\t\t\t' + linha if linha.strip() else linha for linha in xml.split('\n')])
        xml = header + '\n' + xml_indentado + '\n' + footer
    
    # Verifica se deve minificar (verifica se formato_var existe)
    try:
        if formato_var.get() == "minify":
            xml = minificar_xml(xml)
    except:
        pass  # formato_var ainda não foi criado
    
    campo_resultado.insert(tk.END, xml)
    aplicar_formatacao_tags_especificas()
    
    # Atualiza números de linha
    if atualizar_numeros_linha_func:
        atualizar_numeros_linha_func()

def minificar_xml(xml):
    """Remove espaços e quebras de linha do XML"""
    # Remove quebras de linha e espaços entre tags
    xml_minificado = re.sub(r'>\s+<', '><', xml)
    # Remove espaços no início e fim
    xml_minificado = xml_minificado.strip()
    return xml_minificado

def formatar_xml(xml):
    """Formata o XML com indentação usando tabs, mantendo tags de abertura e fechamento"""
    try:
        # Remove espaços extras e quebras de linha
        xml_limpo = re.sub(r'>\s+<', '><', xml.strip())
        
        resultado = []
        nivel = 0
        i = 0
        
        while i < len(xml_limpo):
            if xml_limpo[i] != '<':
                i += 1
                continue
            
            # Encontra o final desta tag
            fim = xml_limpo.find('>', i)
            if fim == -1:
                break
            
            tag_atual = xml_limpo[i:fim + 1]
            
            # Tag de fechamento (apenas para tags com filhos)
            if tag_atual.startswith('</'):
                nivel -= 1
                resultado.append('\t' * nivel + tag_atual)
                i = fim + 1
                
            # Tag auto-fechada
            elif tag_atual.endswith('/>'):
                resultado.append('\t' * nivel + tag_atual)
                i = fim + 1
                
            # Tag de abertura
            else:
                # Extrai nome da tag
                match = re.match(r'<(\w+)', tag_atual)
                if not match:
                    i = fim + 1
                    continue
                
                nome_tag = match.group(1)
                tag_fechamento = f'</{nome_tag}>'
                
                # Busca o conteúdo até a próxima tag '<'
                proximo_tag_idx = xml_limpo.find('<', fim + 1)
                
                if proximo_tag_idx == -1:
                    resultado.append('\t' * nivel + tag_atual)
                    i = fim + 1
                    continue
                
                conteudo_entre = xml_limpo[fim + 1:proximo_tag_idx]
                proxima_tag_fim = xml_limpo.find('>', proximo_tag_idx)
                if proxima_tag_fim == -1:
                    resultado.append('\t' * nivel + tag_atual)
                    i = fim + 1
                    continue
                    
                proxima_tag = xml_limpo[proximo_tag_idx:proxima_tag_fim + 1]
                
                # Verifica se a próxima tag é exatamente o fechamento desta tag
                if proxima_tag == tag_fechamento:
                    # Tag vazia ou com conteúdo simples - coloca tudo na mesma linha
                    linha_completa = '\t' * nivel + tag_atual + conteudo_entre + tag_fechamento
                    resultado.append(linha_completa)
                    i = proxima_tag_fim + 1
                else:
                    # Tag com filhos - quebra de linha e aumenta indentação
                    resultado.append('\t' * nivel + tag_atual)
                    nivel += 1
                    i = fim + 1
        
        return '\n'.join(resultado)
        
    except Exception as e:
        # Se falhar, retorna o XML original
        return xml

def atualizar_formato():
    """Atualiza o formato do XML quando trocar entre formatado e minify"""
    # Pega o conteúdo atual do campo
    conteudo = campo_resultado.get(1.0, tk.END).strip()
    if not conteudo:
        return
    
    # Remove a declaração XML se existir antes de processar
    conteudo_sem_declaracao = re.sub(r'<\?xml[^>]*\?>\s*', '', conteudo)
    
    # Aplica o formato escolhido
    if formato_var.get() == "minify":
        xml_processado = minificar_xml(conteudo_sem_declaracao)
    else:
        xml_processado = formatar_xml(conteudo_sem_declaracao)
    
    # Salva a posição do scroll
    posicao_scroll = campo_resultado.yview()
    
    # Atualiza o campo
    campo_resultado.delete(1.0, tk.END)
    campo_resultado.insert(tk.END, xml_processado)
    
    # Reaplica formatações
    aplicar_formatacao_tags_especificas()
    
    # Atualiza números de linha
    if atualizar_numeros_linha_func:
        atualizar_numeros_linha_func()
    
    # Restaura a posição do scroll
    campo_resultado.yview_moveto(posicao_scroll[0])

def aplicar_tema():
    """Aplica o tema moderno na aplicação com cores suaves e profissionais"""
    global menu_bar, menu_importacoes
    cores = gerenciador_temas.get_cores()
    fonts = gerenciador_temas.get_font_config()
    
    # Atualiza janela principal
    janela.configure(bg=cores["bg"])
    
    # Atualiza campo de resultado com estilo moderno
    campo_resultado.configure(
        bg=cores["text_bg"],
        fg=cores["text_fg"],
        insertbackground=cores["button_bg"],
        selectbackground=cores["select_bg"],
        selectforeground=cores["select_fg"],
        relief=tk.FLAT,
        borderwidth=0,
        highlightthickness=1,
        highlightbackground=cores["border"],
        highlightcolor=cores["entry_focus"]
    )
    
    # Atualiza estilo do ttk
    style = ttk.Style()
    style.theme_use('clam')  # Tema mais customizável
    
    # ===== FRAMES =====
    style.configure("TFrame", 
                   background=cores["bg"])
    
    style.configure("Card.TFrame",
                   background=cores["bg_secondary"],
                   relief=tk.FLAT)
    
    # ===== LABELS =====
    style.configure("TLabel", 
                   background=cores["bg"],
                   foreground=cores["fg"],
                   font=(fonts["family"], fonts["size_normal"]))
    
    style.configure("Title.TLabel",
                   background=cores["bg"],
                   foreground=cores["fg"],
                   font=(fonts["family"], fonts["size_title"], "bold"))
    
    style.configure("Subtitle.TLabel",
                   background=cores["bg"],
                   foreground=cores["fg_secondary"],
                   font=(fonts["family"], fonts["size_medium"]))
    
    # ===== BOTÕES MODERNOS =====
    style.configure("TButton",
                   background=cores["button_bg"],
                   foreground=cores["button_fg"],
                   borderwidth=0,
                   focuscolor=cores["button_bg"],
                   relief=tk.FLAT,
                   font=(fonts["family"], fonts["size_normal"]),
                   padding=(16, 8))
    
    style.map("TButton",
              background=[('!disabled', cores["button_bg"]),
                         ('active', cores["button_hover"]),
                         ('pressed', cores["button_hover"])],
              foreground=[('!disabled', cores["button_fg"]),
                         ('active', cores["button_fg"])])
    
    # Botão secundário
    style.configure("Secondary.TButton",
                   background=cores["button_secondary"],
                   foreground=cores["button_secondary_fg"],
                   borderwidth=0,
                   relief=tk.FLAT,
                   font=(fonts["family"], fonts["size_normal"]),
                   padding=(16, 8))
    
    style.map("Secondary.TButton",
              background=[('!disabled', cores["button_secondary"]),
                         ('active', cores["bg_hover"]),
                         ('pressed', cores["bg_hover"])],
              foreground=[('!disabled', cores["button_secondary_fg"]),
                         ('active', cores["fg"])])

    # ===== COMBOBOX =====
    style.configure("TCombobox",
                   fieldbackground=cores["entry_bg"],
                   background=cores["button_bg"],
                   foreground=cores["text_fg"],
                   arrowcolor=cores["fg_secondary"],
                   borderwidth=1,
                   relief=tk.FLAT)
    
    style.map("TCombobox",
             fieldbackground=[('readonly', cores["entry_bg"])],
             selectbackground=[('readonly', cores["entry_bg"])],
             selectforeground=[('readonly', cores["text_fg"])],
             background=[('readonly', cores["button_bg"]), ('active', cores["button_hover"])],
             arrowcolor=[('readonly', cores["fg_secondary"]), ('active', cores["button_fg"])])
    
    # Combobox dropdown
    janela.option_add('*TCombobox*Listbox.background', cores["menu_bg"])
    janela.option_add('*TCombobox*Listbox.foreground', cores["menu_fg"])
    janela.option_add('*TCombobox*Listbox.selectBackground', cores["select_bg"])
    janela.option_add('*TCombobox*Listbox.selectForeground', cores["select_fg"])
    janela.option_add('*TCombobox*Listbox.font', (fonts["family"], fonts["size_normal"]))

    # ===== RADIOBUTTON =====
    style.configure("TRadiobutton",
                   background=cores["bg"],
                   foreground=cores["fg"],
                   font=(fonts["family"], fonts["size_normal"]))
    
    style.map("TRadiobutton",
             background=[('active', cores["bg"])],
             foreground=[('active', cores["button_bg"])])

    # ===== ENTRY =====
    style.configure("TEntry",
                   fieldbackground=cores["entry_bg"],
                   background=cores["entry_bg"],
                   foreground=cores["text_fg"],
                   borderwidth=1,
                   relief=tk.FLAT,
                   insertcolor=cores["text_fg"])
    
    # ===== TREEVIEW (Tabelas) =====
    style.configure("Treeview",
                   background=cores["text_bg"],
                   foreground=cores["text_fg"],
                   fieldbackground=cores["text_bg"],
                   borderwidth=0,
                   relief=tk.FLAT,
                   font=(fonts["family"], fonts["size_normal"]))
    
    style.configure("Treeview.Heading",
                   background=cores["grid_header_bg"],
                   foreground=cores["grid_header_fg"],
                   borderwidth=0,
                   relief=tk.FLAT,
                   font=(fonts["family"], fonts["size_normal"], "bold"))
    
    style.map("Treeview",
             background=[('selected', cores["grid_row_selected"])],
             foreground=[('selected', cores["text_fg"])])
    
    style.map("Treeview.Heading",
             background=[('active', cores["bg_hover"])],
             foreground=[('active', cores["fg"])])

    # ===== SCROLLBAR PADRONIZADA =====
    style.configure("Vertical.TScrollbar",
                   background=cores["scrollbar_thumb"],
                   troughcolor=cores["scrollbar_bg"],
                   borderwidth=0,
                   arrowsize=12,
                   width=16)
    
    style.map("Vertical.TScrollbar",
             background=[('active', cores["scrollbar_thumb_hover"]),
                        ('pressed', cores["scrollbar_thumb_hover"])])
    
    # Scrollbar horizontal também
    style.configure("Horizontal.TScrollbar",
                   background=cores["scrollbar_thumb"],
                   troughcolor=cores["scrollbar_bg"],
                   borderwidth=0,
                   arrowsize=12,
                   width=16)
    
    style.map("Horizontal.TScrollbar",
             background=[('active', cores["scrollbar_thumb_hover"]),
                        ('pressed', cores["scrollbar_thumb_hover"])])
    
    # Define opções globais para widgets Tk padrão
    janela.option_add('*Background', cores["bg"])
    janela.option_add('*Foreground', cores["fg"])
    janela.option_add('*Entry.Background', cores["entry_bg"])
    janela.option_add('*Entry.Foreground', cores["text_fg"])
    janela.option_add('*Entry.relief', tk.FLAT)
    janela.option_add('*Entry.borderWidth', 1)
    janela.option_add('*Text.Background', cores["text_bg"])
    janela.option_add('*Text.Foreground', cores["text_fg"])
    janela.option_add('*Text.relief', tk.FLAT)
    janela.option_add('*Label.Background', cores["bg"])
    janela.option_add('*Label.Foreground', cores["fg"])
    janela.option_add('*Label.font', (fonts["family"], fonts["size_normal"]))

    # ===== MENU =====
    menu_bar.configure(
        bg=cores["menu_bg"],
        fg=cores["menu_fg"],
        activebackground=cores["button_bg"],
        activeforeground=cores["button_fg"],
        relief=tk.FLAT,
        borderwidth=0,
        font=(fonts["family"], fonts["size_normal"])
    )
    
    menu_importacoes.configure(
        bg=cores["menu_bg"],
        fg=cores["menu_fg"],
        activebackground=cores["menu_hover_bg"],
        activeforeground=cores["button_bg"],
        relief=tk.FLAT,
        borderwidth=0,
        font=(fonts["family"], fonts["size_normal"])
    )
    
    # Reaplica formatações específicas
    aplicar_formatacao_tags_especificas()

def aplicar_formatacao_tags_xml():
    """Aplica coloração azul para todas as tags XML."""
    cores = gerenciador_temas.get_cores()
    
    # Configura tag para tags XML em azul (sem background, apenas foreground)
    # A opção elide=False evita que texto novo herde a tag automaticamente
    campo_resultado.tag_config("tag_xml", foreground="#0066CC")
    
    # Remove formatação antiga
    campo_resultado.tag_remove("tag_xml", "1.0", tk.END)
    
    # Obtém todo o conteúdo
    texto = campo_resultado.get("1.0", tk.END)
    
    # Busca todas as tags usando regex
    # Tag de abertura: <TagName>
    for match in re.finditer(r'<(\w+)>', texto):
        start_pos = match.start()
        end_pos = match.end()
        
        # Converte posição do texto em índice do widget
        linha = texto[:start_pos].count('\n') + 1
        coluna = start_pos - texto[:start_pos].rfind('\n') - 1
        inicio = f"{linha}.{coluna}"
        
        linha_fim = texto[:end_pos].count('\n') + 1
        coluna_fim = end_pos - texto[:end_pos].rfind('\n') - 1
        fim = f"{linha_fim}.{coluna_fim}"
        
        campo_resultado.tag_add("tag_xml", inicio, fim)
    
    # Tag de fechamento: </TagName>
    for match in re.finditer(r'</(\w+)>', texto):
        start_pos = match.start()
        end_pos = match.end()
        
        linha = texto[:start_pos].count('\n') + 1
        coluna = start_pos - texto[:start_pos].rfind('\n') - 1
        inicio = f"{linha}.{coluna}"
        
        linha_fim = texto[:end_pos].count('\n') + 1
        coluna_fim = end_pos - texto[:end_pos].rfind('\n') - 1
        fim = f"{linha_fim}.{coluna_fim}"
        
        campo_resultado.tag_add("tag_xml", inicio, fim)
    
    # Tag auto-fechada: <TagName/>
    for match in re.finditer(r'<(\w+)/>', texto):
        start_pos = match.start()
        end_pos = match.end()
        
        linha = texto[:start_pos].count('\n') + 1
        coluna = start_pos - texto[:start_pos].rfind('\n') - 1
        inicio = f"{linha}.{coluna}"
        
        linha_fim = texto[:end_pos].count('\n') + 1
        coluna_fim = end_pos - texto[:end_pos].rfind('\n') - 1
        fim = f"{linha_fim}.{coluna_fim}"
        
        campo_resultado.tag_add("tag_xml", inicio, fim)

def aplicar_formatacao_tags_especificas():
    """Aplica formatação de cor apenas nas tags específicas com estilo moderno."""
    # Primeiro aplica coloração azul para todas as tags XML
    aplicar_formatacao_tags_xml()
    
    # Define a prioridade da tag de coloração XML para ser a mais baixa
    # Isso garante que outras formatações (verde, vermelho, amarelo) tenham precedência
    campo_resultado.tag_lower("tag_xml")
    
    # 1. Configura as cores das tags (background moderno)
    cores = gerenciador_temas.get_cores()
    campo_resultado.tag_config("verde_claro", 
                              background=cores["tag_verde"],
                              foreground=cores["text_fg"])
    campo_resultado.tag_config("vermelho_claro", 
                              background=cores["tag_vermelho"],
                              foreground=cores["text_fg"])

    # 2. Remove formatações antigas para não sobrepor ao gerar novo XML
    campo_resultado.tag_remove("verde_claro", "1.0", tk.END)
    campo_resultado.tag_remove("vermelho_claro", "1.0", tk.END)

    def destacar_padrao(regex, nome_tag_formatacao):
        posicao_inicial = "1.0"
        while True:
            # Busca no widget usando regex do próprio Tkinter
            posicao_inicial = campo_resultado.search(regex, posicao_inicial, stopindex=tk.END, regexp=True)
            if not posicao_inicial:
                break
            
            # Obtém o conteúdo capturado para saber o tamanho exato da tag
            match_texto = campo_resultado.get(posicao_inicial, f"{posicao_inicial} lineend")
            match_res = re.search(regex, match_texto)
            
            if match_res:
                tamanho = len(match_res.group(0))
                posicao_final = f"{posicao_inicial} + {tamanho} chars"
                
                # Adiciona a cor apenas no intervalo da tag capturada
                campo_resultado.tag_add(nome_tag_formatacao, posicao_inicial, posicao_final)
                
                # Move para a próxima posição após este match
                posicao_inicial = posicao_final
            else:
                posicao_inicial = f"{posicao_inicial} + 1 char"

    # Regex explicada:
    # </? -> opcionalmente começa com / (fechamento)
    # [^>]* -> qualquer caractere que não seja o fechamento da tag >
    # (Acto|Recsd)> -> termina obrigatoriamente com Acto ou Recsd seguido de >
    destacar_padrao(r"</?[^>]*Acto>", "verde_claro")
    destacar_padrao(r"</?[^>]*Recsd>", "vermelho_claro")

    # Chama a próxima formatação
    aplicar_formatacao_dominios()

def aplicar_formatacao_dominios():
    """Aplica formatação nas tags com domínio (amarelo) e adiciona ícones de informação visuais (não fazem parte do texto)."""
    # Configura tags de formatação
    cores = gerenciador_temas.get_cores()
    campo_resultado.tag_config("dominio", 
                              background=cores["tag_amarelo"],
                              foreground=cores["text_fg"])
    campo_resultado.tag_config("dominio_link", 
                              foreground=cores["tag_link"],
                              underline=1)
    
    # Procura por padrão ⟪...⟫ (domínios) no texto
    texto = campo_resultado.get(1.0, tk.END)
    linhas = texto.split('\n')
    
    for i, linha in enumerate(linhas):
        # Processa domínios (⟪...⟫)
        if '⟪...⟫' in linha:
            # Extrai o nome da tag
            match = re.search(r'<(\w+)>⟪\.\.\.⟫</(\w+)>', linha)
            if match:
                nome_tag = match.group(1)
                # Calcula posição no widget
                start_idx = f"{i+1}.{linha.find('⟪')}"
                end_idx = f"{i+1}.{linha.find('⟫')+1}"
                
                # Substitui o marcador por ...
                campo_resultado.delete(start_idx, end_idx)
                campo_resultado.insert(start_idx, "...")
                
                # Aplica formatação de domínio
                new_end = f"{i+1}.{linha.find('⟪')+3}"
                campo_resultado.tag_add("dominio", start_idx, new_end)
                campo_resultado.tag_add("dominio_link", start_idx, new_end)
                campo_resultado.tag_add(f"tag_{nome_tag}", start_idx, new_end)
                
                # Adiciona binding para clique
                campo_resultado.tag_bind(f"tag_{nome_tag}", "<Button-1>", 
                                        lambda e, tag=nome_tag: mostrar_dominio(tag))
                campo_resultado.tag_bind(f"tag_{nome_tag}", "<Enter>", 
                                        lambda e: campo_resultado.config(cursor="hand2"))
                campo_resultado.tag_bind(f"tag_{nome_tag}", "<Leave>", 
                                        lambda e: campo_resultado.config(cursor=""))
    
    # Processa ícones de informação - adiciona ícones VISUAIS que não fazem parte do texto
    # Recarrega o texto atualizado
    texto = campo_resultado.get(1.0, tk.END)
    
    # Para cada tag cadastrada como informação, procura por tags vazias e adiciona ícone visual
    for nome_tag, dados in parser.DOMINIOS.items():
        tipo = dados.get("tipo", "dominio")
        
        if tipo == "informacao":
            # Procura por padrão <NomeTag></NomeTag> (tag vazia)
            padrao = f'<{nome_tag}></{nome_tag}>'
            
            # Encontra todas as ocorrências no texto
            inicio_busca = 0
            contador = 0
            while True:
                pos = texto.find(padrao, inicio_busca)
                if pos == -1:
                    break
                
                # Converte posição linear para linha.coluna
                linhas_antes = texto[:pos].count('\n')
                col_inicio = pos - texto[:pos].rfind('\n') - 1
                
                # Posição logo após o fechamento da tag
                tamanho_tag = len(padrao)
                posicao_icone = f"{linhas_antes+1}.{col_inicio + tamanho_tag}"
                
                # Cria um Label com o ícone (não faz parte do texto)
                icone_label = tk.Label(campo_resultado, 
                                      text=" ℹ️",
                                      fg="#2874A6",  # Azul mais escuro para destacar
                                      bg=cores["text_bg"],
                                      font=("Segoe UI Emoji", 9),
                                      cursor="hand2")
                
                tag_unica = f"info_icone_{nome_tag}_{contador}"
                
                # Adiciona bindings ao label
                icone_label.bind("<Enter>", 
                               lambda e, tag=nome_tag, lbl=icone_label: mostrar_tooltip_informacao_do_label(tag, lbl))
                icone_label.bind("<Leave>", 
                               lambda e: fechar_tooltip_informacao())
                icone_label.bind("<Button-1>", 
                               lambda e, tag=nome_tag, lbl=icone_label: mostrar_tooltip_informacao_do_label(tag, lbl))
                
                # Insere o label como uma "janela" no Text widget - não faz parte do texto!
                try:
                    campo_resultado.window_create(posicao_icone, window=icone_label)
                except:
                    pass  # Se a posição não existe mais, ignora
                
                inicio_busca = pos + len(padrao)
                contador += 1
    
    # Aplica formatação também nas tags que já possuem valores
    aplicar_formatacao_dominios_com_valor()

def aplicar_formatacao_dominios_com_valor():
    """Aplica formatação nas tags que já possuem valores de domínio preenchidos.
    Tags de informação não são formatadas aqui pois devem permanecer vazias."""
    cores = gerenciador_temas.get_cores()
    campo_resultado.tag_config("dominio", 
                              background=cores["tag_amarelo"],
                              foreground=cores["text_fg"])
    
    # Percorre apenas os domínios (não informações)
    for nome_tag, dados in parser.DOMINIOS.items():
        tipo = dados.get("tipo", "dominio")
        
        # Pula tags de informação (elas devem ficar vazias e com formatação diferente)
        if tipo == "informacao":
            continue
        
        # Busca todas as ocorrências dessa tag no texto
        padrao = f'<{nome_tag}>([^<]+)</{nome_tag}>'
        texto = campo_resultado.get(1.0, tk.END)
        
        # Encontra todas as correspondências
        for match in re.finditer(padrao, texto):
            valor = match.group(1)
            
            # Calcula a posição do valor no widget
            # Conta quantos caracteres existem antes do match
            inicio_match = match.start() + len(f'<{nome_tag}>')
            
            # Converte posição linear para linha.coluna
            linhas_antes = texto[:inicio_match].count('\n')
            col = inicio_match - texto[:inicio_match].rfind('\n') - 1
            
            start_idx = f"{linhas_antes+1}.{col}"
            end_idx = f"{linhas_antes+1}.{col+len(valor)}"
            
            # Aplica formatação amarela para domínios
            campo_resultado.tag_add("dominio", start_idx, end_idx)
            campo_resultado.tag_add(f"tag_{nome_tag}_valor", start_idx, end_idx)
            
            # Adiciona binding para permitir trocar o valor
            campo_resultado.tag_bind(f"tag_{nome_tag}_valor", "<Button-1>", 
                                    lambda e, tag=nome_tag: mostrar_dominio(tag))
            campo_resultado.tag_bind(f"tag_{nome_tag}_valor", "<Enter>", 
                                    lambda e: campo_resultado.config(cursor="hand2"))
            campo_resultado.tag_bind(f"tag_{nome_tag}_valor", "<Leave>", 
                                    lambda e: campo_resultado.config(cursor=""))

def mostrar_dominio(nome_tag):
    """Mostra janela popup com os domínios possíveis para a tag (design moderno)"""
    if nome_tag not in parser.DOMINIOS:
        messagebox.showinfo("Domínio", f"Tag '{nome_tag}' não possui domínios cadastrados.")
        return
    
    dominio = parser.DOMINIOS[nome_tag]
    tipo = dominio.get("tipo", "dominio")
    
    # Se for tipo informação, não mostra janela de seleção (já tem tooltip)
    if tipo == "informacao":
        return
    
    # Cria janela popup
    popup = tk.Toplevel(janela)
    cores = gerenciador_temas.get_cores()
    fonts = gerenciador_temas.get_font_config()
    spacing = gerenciador_temas.get_spacing_config()
    
    popup.configure(bg=cores["bg"])
    popup.title(f"Domínio: {nome_tag}")
    
    largura = 700
    altura = 500
    x = janela.winfo_x() + (janela.winfo_width() // 2) - (largura // 2)
    y = janela.winfo_y() + (janela.winfo_height() // 2) - (altura // 2)
    popup.geometry(f"{largura}x{altura}+{x}+{y}")
    popup.minsize(600, 400)
    
    # Frame de cabeçalho com estilo moderno
    frame_header = tk.Frame(popup, bg=cores["bg_secondary"], relief=tk.FLAT)
    frame_header.pack(fill=tk.X, padx=spacing["lg"], pady=(spacing["lg"], spacing["md"]))
    
    # Título
    tk.Label(frame_header, 
             text=dominio.get('tag', nome_tag),
             bg=cores["bg_secondary"],
             fg=cores["fg"],
             font=(fonts["family"], fonts["size_title"], "bold")).pack(anchor="w", pady=(spacing["sm"], 2))
    
    # Seção
    tk.Label(frame_header,
             text=f"Seção: {dominio.get('secao', 'N/A')}",
             bg=cores["bg_secondary"],
             fg=cores["fg_secondary"],
             font=(fonts["family"], fonts["size_normal"])).pack(anchor="w")
    
    # Separador
    tk.Frame(popup, height=1, bg=cores["border"]).pack(fill=tk.X, padx=spacing["lg"])
    
    # Dica com ícone
    frame_dica = tk.Frame(popup, bg=cores["bg"], relief=tk.FLAT)
    frame_dica.pack(fill=tk.X, padx=spacing["lg"], pady=spacing["md"])
    
    tk.Label(frame_dica,
             text="💡",
             bg=cores["bg"],
             font=(fonts["family"], fonts["size_large"])).pack(side=tk.LEFT, padx=(0, spacing["sm"]))
    
    tk.Label(frame_dica,
             text="Clique duas vezes na opção desejada para preencher o XML",
             bg=cores["bg"],
             fg=cores["fg_secondary"],
             font=(fonts["family"], fonts["size_small"], "italic")).pack(side=tk.LEFT, anchor="w")
    
    # Frame para tabela com borda
    frame_tree_container = tk.Frame(popup, bg=cores["border"], relief=tk.FLAT)
    frame_tree_container.pack(fill=tk.BOTH, expand=True, padx=spacing["lg"], pady=(0, spacing["md"]))
    
    frame_tree = tk.Frame(frame_tree_container, bg=cores["text_bg"])
    frame_tree.pack(fill=tk.BOTH, expand=True, padx=1, pady=1)
    
    # Scrollbar
    scroll_y = ttk.Scrollbar(frame_tree, orient=tk.VERTICAL)
    scroll_y.pack(side=tk.RIGHT, fill=tk.Y)
    
    # Treeview com estilo moderno
    tree = ttk.Treeview(frame_tree, columns=("valor", "descricao"), 
                        show="headings", yscrollcommand=scroll_y.set,
                        height=12)
    tree.heading("valor", text="Valor")
    tree.heading("descricao", text="Descrição")
    tree.column("valor", width=100, anchor="center")
    tree.column("descricao", width=500, anchor="w")
    tree.pack(fill=tk.BOTH, expand=True)
    
    scroll_y.config(command=tree.yview)
    
    # Insere opções com estilo alternado
    opcoes = dominio.get('opcoes', [])
    for i, opcao in enumerate(opcoes):
        tags = ('oddrow',) if i % 2 else ('evenrow',)
        tree.insert("", tk.END, values=(opcao.get('valor', ''), opcao.get('descricao', '')), tags=tags)
    
    # Configura cores alternadas para as linhas
    tree.tag_configure('oddrow', background=cores["text_bg"])
    tree.tag_configure('evenrow', background=cores["bg_hover"])
    
    def selecionar_opcao(event):
        """Preenche o valor no XML ao dar duplo clique"""
        selecao = tree.selection()
        if not selecao:
            return
        
        # Pega o valor selecionado
        item = tree.item(selecao[0])
        valor_selecionado = item['values'][0]
        
        # Busca no texto pela tag e substitui o valor (ou ...) mantendo a formatação
        texto = campo_resultado.get(1.0, tk.END)
        
        # Padrão para encontrar a tag com qualquer conteúdo entre as tags (... ou valor existente)
        padrao_com_valor = f'<{nome_tag}>[^<]*</{nome_tag}>'
        
        # Substitui mantendo as tags
        novo_texto = re.sub(padrao_com_valor, f'<{nome_tag}>{valor_selecionado}</{nome_tag}>', texto)
        
        # Atualiza o campo
        campo_resultado.delete(1.0, tk.END)
        campo_resultado.insert(1.0, novo_texto)
        
        # Reaplica as formatações
        aplicar_formatacao_tags_especificas()
        aplicar_formatacao_dominios_com_valor()
        
        # Atualiza números de linha
        if atualizar_numeros_linha_func:
            atualizar_numeros_linha_func()
        
        popup.destroy()
    
    # Bind duplo clique
    tree.bind('<Double-1>', selecionar_opcao)
    
    # Frame inferior para botão
    frame_footer = tk.Frame(popup, bg=cores["bg"])
    frame_footer.pack(fill=tk.X, padx=spacing["lg"], pady=(spacing["md"], spacing["lg"]))
    
    # Botão fechar com estilo secundário
    btn_fechar = ttk.Button(frame_footer, text="Fechar", command=popup.destroy, style="Secondary.TButton")
    btn_fechar.pack(side=tk.RIGHT)

# Variável global para controlar o tooltip de informação
tooltip_informacao_window = None

def mostrar_tooltip_informacao_do_label(nome_tag, label_widget):
    """Mostra tooltip flutuante SEMPRE À DIREITA do label do ícone (design moderno)"""
    global tooltip_informacao_window
    
    # Fecha tooltip anterior se existir
    fechar_tooltip_informacao()
    
    if nome_tag not in parser.DOMINIOS:
        return
    
    informacao = parser.DOMINIOS[nome_tag]
    tipo = informacao.get("tipo", "dominio")
    
    # Só mostra tooltip se for tipo informação
    if tipo != "informacao":
        return
    
    # Pega as descrições (todas devem ter valor "Info")
    opcoes = informacao.get('opcoes', [])
    if not opcoes:
        return
    
    # Combina todas as descrições em um texto
    descricoes = [opcao.get('descricao', '') for opcao in opcoes]
    texto_info = '\n'.join(descricoes)
    
    # Obtém a posição do label na tela
    try:
        # Atualiza para garantir que as coordenadas estão corretas
        label_widget.update_idletasks()
        
        # Posição do label na tela
        x_label = label_widget.winfo_rootx()
        y_label = label_widget.winfo_rooty()
        largura_label = label_widget.winfo_width()
        
        # Posiciona SEMPRE À DIREITA do ícone
        x_tela = x_label + largura_label + 5  # 5px à direita do ícone
        y_tela = y_label
        
    except:
        # Se falhar, não mostra o tooltip
        return
    
    # Cria janela tooltip
    tooltip_informacao_window = tk.Toplevel(janela)
    tooltip_informacao_window.wm_overrideredirect(True)  # Remove borda da janela
    tooltip_informacao_window.wm_attributes("-topmost", True)  # Sempre no topo
    
    # Obtém configurações de tema
    cores = gerenciador_temas.get_cores()
    fonts = gerenciador_temas.get_font_config()
    spacing = gerenciador_temas.get_spacing_config()
    
    # Frame principal com borda e sombra
    frame_principal = tk.Frame(tooltip_informacao_window, 
                              bg="#E8F4F8",  # Azul muito claro
                              relief=tk.SOLID,
                              borderwidth=2,
                              highlightbackground="#3498DB",  # Borda azul
                              highlightthickness=1)
    frame_principal.pack(fill=tk.BOTH, expand=True)
    
    # Cabeçalho com ícone
    frame_header = tk.Frame(frame_principal, bg="#3498DB", height=30)
    frame_header.pack(fill=tk.X, padx=0, pady=0)
    
    tk.Label(frame_header, 
            text=f"ℹ️  {informacao.get('tag', nome_tag)}",
            bg="#3498DB",
            fg="white",
            font=(fonts["family"], fonts["size_normal"], "bold")).pack(side=tk.LEFT, padx=spacing["sm"], pady=4)
    
    # Conteúdo
    frame_conteudo = tk.Frame(frame_principal, bg="#E8F4F8")
    frame_conteudo.pack(fill=tk.BOTH, expand=True, padx=spacing["md"], pady=spacing["md"])
    
    # Texto da informação com quebra de linha
    label_info = tk.Label(frame_conteudo,
                         text=texto_info,
                         bg="#E8F4F8",
                         fg="#21618C",  # Azul escuro
                         font=(fonts["family"], fonts["size_normal"]),
                         justify=tk.LEFT,
                         wraplength=350,  # Quebra de linha
                         anchor="w")
    label_info.pack(fill=tk.BOTH, expand=True)
    
    # Atualiza geometria para obter tamanho real
    tooltip_informacao_window.update_idletasks()
    largura = tooltip_informacao_window.winfo_width()
    altura = tooltip_informacao_window.winfo_height()
    
    # Ajusta para não sair da tela
    largura_tela = tooltip_informacao_window.winfo_screenwidth()
    altura_tela = tooltip_informacao_window.winfo_screenheight()
    
    # Se não couber à direita, mantém à direita mesmo assim (prioridade)
    # Apenas ajusta verticalmente se necessário
    if y_tela + altura > altura_tela:
        y_tela = altura_tela - altura - 10
    
    tooltip_informacao_window.wm_geometry(f"+{x_tela}+{y_tela}")

def mostrar_tooltip_informacao_fixo(nome_tag, indice_icone):
    """Mostra tooltip flutuante fixo ao lado do ícone de informação (design moderno)"""
    global tooltip_informacao_window
    
    # Fecha tooltip anterior se existir
    fechar_tooltip_informacao()
    
    if nome_tag not in parser.DOMINIOS:
        return
    
    informacao = parser.DOMINIOS[nome_tag]
    tipo = informacao.get("tipo", "dominio")
    
    # Só mostra tooltip se for tipo informação
    if tipo != "informacao":
        return
    
    # Pega as descrições (todas devem ter valor "Info")
    opcoes = informacao.get('opcoes', [])
    if not opcoes:
        return
    
    # Combina todas as descrições em um texto
    descricoes = [opcao.get('descricao', '') for opcao in opcoes]
    texto_info = '\n'.join(descricoes)
    
    # Obtém a posição do ícone no widget
    try:
        bbox = campo_resultado.bbox(indice_icone)
        if not bbox:
            return
        
        x_widget, y_widget, _, _ = bbox
        
        # Converte para coordenadas da tela
        x_tela = campo_resultado.winfo_rootx() + x_widget + 20  # 20px à direita do ícone
        y_tela = campo_resultado.winfo_rooty() + y_widget
        
    except:
        # Se falhar ao obter bbox, volta para comportamento baseado no cursor
        return
    
    # Cria janela tooltip
    tooltip_informacao_window = tk.Toplevel(janela)
    tooltip_informacao_window.wm_overrideredirect(True)  # Remove borda da janela
    tooltip_informacao_window.wm_attributes("-topmost", True)  # Sempre no topo
    
    # Obtém configurações de tema
    cores = gerenciador_temas.get_cores()
    fonts = gerenciador_temas.get_font_config()
    spacing = gerenciador_temas.get_spacing_config()
    
    # Frame principal com borda e sombra
    frame_principal = tk.Frame(tooltip_informacao_window, 
                              bg="#E8F4F8",  # Azul muito claro
                              relief=tk.SOLID,
                              borderwidth=2,
                              highlightbackground="#3498DB",  # Borda azul
                              highlightthickness=1)
    frame_principal.pack(fill=tk.BOTH, expand=True)
    
    # Cabeçalho com ícone
    frame_header = tk.Frame(frame_principal, bg="#3498DB", height=30)
    frame_header.pack(fill=tk.X, padx=0, pady=0)
    
    tk.Label(frame_header, 
            text=f"ℹ️  {informacao.get('tag', nome_tag)}",
            bg="#3498DB",
            fg="white",
            font=(fonts["family"], fonts["size_normal"], "bold")).pack(side=tk.LEFT, padx=spacing["sm"], pady=4)
    
    # Conteúdo
    frame_conteudo = tk.Frame(frame_principal, bg="#E8F4F8")
    frame_conteudo.pack(fill=tk.BOTH, expand=True, padx=spacing["md"], pady=spacing["md"])
    
    # Texto da informação com quebra de linha
    label_info = tk.Label(frame_conteudo,
                         text=texto_info,
                         bg="#E8F4F8",
                         fg="#21618C",  # Azul escuro
                         font=(fonts["family"], fonts["size_normal"]),
                         justify=tk.LEFT,
                         wraplength=350,  # Quebra de linha
                         anchor="w")
    label_info.pack(fill=tk.BOTH, expand=True)
    
    # Atualiza geometria para obter tamanho real
    tooltip_informacao_window.update_idletasks()
    largura = tooltip_informacao_window.winfo_width()
    altura = tooltip_informacao_window.winfo_height()
    
    # Ajusta para não sair da tela
    largura_tela = tooltip_informacao_window.winfo_screenwidth()
    altura_tela = tooltip_informacao_window.winfo_screenheight()
    
    if x_tela + largura > largura_tela:
        x_tela = x_tela - largura - 40  # Mostra à esquerda do ícone se não couber à direita
    if y_tela + altura > altura_tela:
        y_tela = altura_tela - altura - 10
    
    tooltip_informacao_window.wm_geometry(f"+{x_tela}+{y_tela}")

def mostrar_tooltip_informacao(event, nome_tag):
    """Mostra tooltip flutuante com informações da tag (design moderno) - versão baseada em evento"""
    global tooltip_informacao_window
    
    # Fecha tooltip anterior se existir
    fechar_tooltip_informacao()
    
    if nome_tag not in parser.DOMINIOS:
        return
    
    informacao = parser.DOMINIOS[nome_tag]
    tipo = informacao.get("tipo", "dominio")
    
    # Só mostra tooltip se for tipo informação
    if tipo != "informacao":
        return
    
    # Pega as descrições (todas devem ter valor "Info")
    opcoes = informacao.get('opcoes', [])
    if not opcoes:
        return
    
    # Combina todas as descrições em um texto
    descricoes = [opcao.get('descricao', '') for opcao in opcoes]
    texto_info = '\n'.join(descricoes)
    
    # Cria janela tooltip
    tooltip_informacao_window = tk.Toplevel(janela)
    tooltip_informacao_window.wm_overrideredirect(True)  # Remove borda da janela
    tooltip_informacao_window.wm_attributes("-topmost", True)  # Sempre no topo
    
    # Obtém configurações de tema
    cores = gerenciador_temas.get_cores()
    fonts = gerenciador_temas.get_font_config()
    spacing = gerenciador_temas.get_spacing_config()
    
    # Frame principal com borda e sombra
    frame_principal = tk.Frame(tooltip_informacao_window, 
                              bg="#E8F4F8",  # Azul muito claro
                              relief=tk.SOLID,
                              borderwidth=2,
                              highlightbackground="#3498DB",  # Borda azul
                              highlightthickness=1)
    frame_principal.pack(fill=tk.BOTH, expand=True)
    
    # Cabeçalho com ícone
    frame_header = tk.Frame(frame_principal, bg="#3498DB", height=30)
    frame_header.pack(fill=tk.X, padx=0, pady=0)
    
    tk.Label(frame_header, 
            text=f"ℹ️  {informacao.get('tag', nome_tag)}",
            bg="#3498DB",
            fg="white",
            font=(fonts["family"], fonts["size_normal"], "bold")).pack(side=tk.LEFT, padx=spacing["sm"], pady=4)
    
    # Conteúdo
    frame_conteudo = tk.Frame(frame_principal, bg="#E8F4F8")
    frame_conteudo.pack(fill=tk.BOTH, expand=True, padx=spacing["md"], pady=spacing["md"])
    
    # Texto da informação com quebra de linha
    label_info = tk.Label(frame_conteudo,
                         text=texto_info,
                         bg="#E8F4F8",
                         fg="#21618C",  # Azul escuro
                         font=(fonts["family"], fonts["size_normal"]),
                         justify=tk.LEFT,
                         wraplength=350,  # Quebra de linha
                         anchor="w")
    label_info.pack(fill=tk.BOTH, expand=True)
    
    # Posiciona o tooltip perto do cursor
    x = event.x_root + 15
    y = event.y_root + 15
    
    # Ajusta para não sair da tela
    tooltip_informacao_window.update_idletasks()
    largura = tooltip_informacao_window.winfo_width()
    altura = tooltip_informacao_window.winfo_height()
    
    largura_tela = tooltip_informacao_window.winfo_screenwidth()
    altura_tela = tooltip_informacao_window.winfo_screenheight()
    
    if x + largura > largura_tela:
        x = largura_tela - largura - 10
    if y + altura > altura_tela:
        y = altura_tela - altura - 10
    
    tooltip_informacao_window.wm_geometry(f"+{x}+{y}")

def fechar_tooltip_informacao():
    """Fecha o tooltip de informação"""
    global tooltip_informacao_window
    
    if tooltip_informacao_window:
        tooltip_informacao_window.destroy()
        tooltip_informacao_window = None

def importar_e_atualizar():
    parser.selecionar_arquivos_xsd()
    combo["values"] = parser.TAGS_XML
    if parser.TAGS_XML:
        tag_var.set(parser.TAGS_XML[0])

def agrupar_por_grupo(tags):
    if not tags:
        return {}

    # A primeira tag é a raiz da mensagem, que não deve ser um grupo.
    # A estrutura principal é um dicionário que conterá os grupos.
    estrutura_base = {tags[0]: ""}
    pilha = [(estrutura_base, tags[0])]  # (dicionario_pai, nome_pai)

    # Itera a partir da segunda tag
    for tag in tags[1:]:
        tag = tag.strip()
        if not tag:
            continue

        # Se for uma tag de grupo, cria um novo nível
        if tag.startswith("Grupo_"):
            novo_grupo = {}
            pai_atual, nome_pai_atual = pilha[-1]

            # Verifica se o grupo já existe no pai
            if tag in pai_atual:
                # Se já existe e não é uma lista, transforma em lista
                if not isinstance(pai_atual[tag], list):
                    pai_atual[tag] = [pai_atual[tag]]
                # Adiciona o novo grupo à lista
                pai_atual[tag].append(novo_grupo)
            else:
                # Se não existe, cria como um novo dicionário
                pai_atual[tag] = novo_grupo
            
            # Empilha o novo grupo para que ele se torne o pai dos próximos elementos
            pilha.append((novo_grupo, tag))

        # Se for uma tag de fechamento de grupo
        elif tag.startswith("/Grupo_"):
            tag_fechamento = tag.lstrip("/")
            # Se a tag de fechamento corresponde ao topo da pilha, desempilha
            if pilha and pilha[-1][1] == tag_fechamento:
                pilha.pop()

        # Se for uma tag normal (não é grupo nem fechamento de grupo)
        elif not tag.startswith("/"):
            # Adiciona a tag ao dicionário do grupo que está no topo da pilha
            if pilha:
                pai_atual, _ = pilha[-1]
                pai_atual[tag] = ""
            
    return estrutura_base

def abrir_tela_tags_para_json():
    janela_tags = tk.Toplevel(janela)
    cores = gerenciador_temas.get_cores()
    janela_tags.configure(bg=cores["bg"])
    janela_tags.title("Transformar Tags em JSON")
    largura = 600
    altura = 630
    largura_tela = janela.winfo_screenwidth()
    altura_tela = janela.winfo_screenheight()
    x = (largura_tela // 2) - (largura // 2)
    y = (altura_tela // 2) - (altura // 2)
    janela_tags.geometry(f"{largura}x{altura}+{x}+{y}")
    janela_tags.minsize(550, 530)
    
    # Configura o grid da janela principal para controlar o redimensionamento
    janela_tags.columnconfigure(0, weight=1)
    janela_tags.rowconfigure(0, weight=0)  # Label status - fixo
    janela_tags.rowconfigure(1, weight=0)  # Label "Cole..." - fixo
    janela_tags.rowconfigure(2, weight=1)  # Campo input - expansível
    janela_tags.rowconfigure(3, weight=0)  # Botão "Extrair Tags" - fixo
    janela_tags.rowconfigure(4, weight=0)  # Label "Tags encontradas" - fixo
    janela_tags.rowconfigure(5, weight=2)  # Campo resultado - expansível (maior)
    janela_tags.rowconfigure(6, weight=0)  # Frame inferior - fixo
    
    # Label de Status (LINHA 0 - FIXO)
    label_status = ttk.Label(janela_tags, text="", font=("Arial", 9), foreground="blue")
    label_status.grid(row=0, column=0, sticky='ew', padx=10, pady=(5, 0))
    
    def atualizar_status(mensagem, cor="blue"):
        """Atualiza a mensagem de status"""
        label_status.config(text=mensagem, foreground=cor)
        # Limpa a mensagem após 5 segundos
        janela_tags.after(5000, lambda: label_status.config(text=""))
    
    def limpar_tags():
        texto_original = campo_input.get("1.0", tk.END)
        tags = re.findall(r"<[^>]+>", texto_original)
        tags_filtradas = []
        for tag in tags:
            nome = tag.strip("<>")
            if nome:
                tags_filtradas.append(nome)
        campo_resultado_tags.delete("1.0", tk.END)
        campo_resultado_tags.insert("1.0", "\n".join(tags_filtradas))
        if tags_filtradas:
            atualizar_status(f"{len(tags_filtradas)} tag(s) extraída(s).", "green")
        else:
            atualizar_status("Nenhuma tag encontrada.", "orange")

    def incluir_no_json():
        nome_msg = entrada_nome.get().strip()
        if not nome_msg:
            atualizar_status("Digite o nome da mensagem (ex: DDA0001E).", "red")
            entrada_nome.focus()
            return
        linhas = campo_resultado_tags.get("1.0", tk.END).splitlines()
        tags_limpas = [linha.strip() for linha in linhas if linha.strip()]
        tags_para_processar = tags_limpas

        # Se a primeira linha for a tag raiz, remove abertura e fechamento
        if tags_limpas and nome_msg == tags_limpas[0]:
            tags_para_processar = tags_limpas[1:-1]

        if not tags_para_processar:
            atualizar_status("Nenhuma tag encontrada para incluir.", "orange")
            return

        estrutura = agrupar_por_grupo(tags_para_processar)

        # Obtém o caminho do arquivo (pergunta ao usuário se necessário)
        json_path = config_manager.obter_caminho_arquivo("estrutura_layouts.json")
        if not json_path:
            atualizar_status("Operação cancelada.", "orange")
            return
        
        templates = {}
        if os.path.exists(json_path):
            with open(json_path, "r", encoding="utf-8") as f:
                atual = json.load(f)
                # Preserva os templates se existirem
                templates = atual.pop("_templates", {})
        else:
            atual = {}

        atual[nome_msg] = estrutura
        
        # Adiciona os templates de volta antes de salvar
        if templates:
            atual["_templates"] = templates

        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(atual, f, indent=2, ensure_ascii=False)

        parser.carregar_json()
        combo["values"] = parser.TAGS_XML
        if parser.TAGS_XML:
            tag_var.set(parser.TAGS_XML[0])
        
        atualizar_status(f"Estrutura salva em: {json_path}", "green")

        atualizar_status(f"Mensagem '{nome_msg}' incluída com sucesso no JSON!", "green")

    tk.Label(janela_tags, text="Cole abaixo o conteúdo com as tags:",
             bg=cores["bg"], fg=cores["fg"]).grid(row=1, column=0, sticky='w', padx=10, pady=(10, 2))
    campo_input = scrolledtext.ScrolledText(janela_tags, width=70, height=10)
    campo_input.grid(row=2, column=0, sticky='nsew', padx=10, pady=5)

    botao_limpar = ttk.Button(janela_tags, text="Extrair Tags", command=limpar_tags)
    botao_limpar.grid(row=3, column=0, pady=5)

    tk.Label(janela_tags, text="Tags encontradas:",
             bg=cores["bg"], fg=cores["fg"]).grid(row=4, column=0, sticky='w', padx=10)
    campo_resultado_tags = scrolledtext.ScrolledText(janela_tags, width=70, height=15)
    campo_resultado_tags.grid(row=5, column=0, sticky='nsew', padx=10, pady=5)

    frame_inferior = ttk.Frame(janela_tags)
    frame_inferior.grid(row=6, column=0, sticky='ew', pady=10)

    tk.Label(frame_inferior, text="Nome da mensagem:",
             bg=cores["bg"], fg=cores["fg"]).grid(row=0, column=0, padx=5)
    entrada_nome = ttk.Entry(frame_inferior)
    entrada_nome.grid(row=0, column=1, padx=5)
    botao_incluir = ttk.Button(frame_inferior, text="Incluir no JSON", command=incluir_no_json)
    botao_incluir.grid(row=0, column=2, padx=10)
    botao_fechar = ttk.Button(frame_inferior, text="Fechar", command=janela_tags.destroy)
    botao_fechar.grid(row=0, column=3, padx=5)

def abrir_tela_inclusao_dominios():
    """Abre a tela para inclusão manual de domínios"""
    janela_dominios = tk.Toplevel(janela)
    janela_dominios.title("Inclusão/Edição de Domínios")
    
    largura = 700
    altura = 550
    largura_tela = janela.winfo_screenwidth()
    altura_tela = janela.winfo_screenheight()
    x = (largura_tela // 2) - (largura // 2)
    y = (altura_tela // 2) - (altura // 2)
    janela_dominios.geometry(f"{largura}x{altura}+{x}+{y}")
    janela_dominios.minsize(600, 500)
    
    # Obtém configurações de tema
    cores = gerenciador_temas.get_cores()
    fonts = gerenciador_temas.get_font_config()
    spacing = gerenciador_temas.get_spacing_config()
    janela_dominios.configure(bg=cores["bg"])
    
    # Configura o grid da janela principal para controlar o redimensionamento
    janela_dominios.columnconfigure(0, weight=1)
    janela_dominios.rowconfigure(0, weight=0)  # Label status - fixo
    janela_dominios.rowconfigure(1, weight=0)  # Frame campos - fixo
    janela_dominios.rowconfigure(2, weight=1)  # Frame grid - expansível
    janela_dominios.rowconfigure(3, weight=0)  # Frame botões grid - fixo
    janela_dominios.rowconfigure(4, weight=0)  # Frame inferior - fixo
    
    # Label de Status (LINHA 0 - FIXO)
    label_status = ttk.Label(janela_dominios, text="", font=("Arial", 9), foreground="blue")
    label_status.grid(row=0, column=0, sticky='ew', padx=10, pady=(5, 0))
    
    def atualizar_status(mensagem, cor="blue"):
        """Atualiza a mensagem de status"""
        label_status.config(text=mensagem, foreground=cor)
        # Limpa a mensagem após 5 segundos
        janela_dominios.after(5000, lambda: label_status.config(text=""))
    
    # Frame superior - campos de entrada (LINHA 1 - FIXO)
    frame_campos = ttk.Frame(janela_dominios, padding=10)
    frame_campos.grid(row=1, column=0, sticky='ew')
    
    ttk.Label(frame_campos, text="Tag:*").grid(row=0, column=0, sticky='w', padx=5, pady=5)
    entrada_tag = ttk.Entry(frame_campos, width=30)
    entrada_tag.grid(row=0, column=1, padx=5, pady=5)
    
    # Botão Buscar ao lado do campo Tag
    def buscar_dominio():
        """Busca e carrega um domínio existente no arquivo JSON"""
        nome_tag = entrada_tag.get().strip()
        
        if not nome_tag:
            atualizar_status("Digite o nome da tag para buscar.", "red")
            entrada_tag.focus()
            return
        
        # Carrega JSON existente
        json_path = config_manager.obter_caminho_arquivo("dominios_DDA.json")
        if not json_path:
            atualizar_status("Operação cancelada.", "orange")
            return
        
        try:
            if not os.path.exists(json_path):
                atualizar_status("Arquivo de domínios não encontrado.", "red")
                return
            
            with open(json_path, "r", encoding="utf-8") as f:
                dominios = json.load(f)
            
            # Busca a tag
            if nome_tag not in dominios:
                atualizar_status(f"Nenhum registro encontrado para a tag '{nome_tag}'.", "orange")
                return
            
            dominio = dominios[nome_tag]
            
            # Preenche os campos
            entrada_descricao_tag.delete(0, tk.END)
            entrada_descricao_tag.insert(0, dominio.get("tag", ""))
            
            # Define tipo registro (compatibilidade com registros antigos)
            tipo_reg = dominio.get("tipo", "dominio")
            tipo_registro_var.set("Domínio" if tipo_reg == "dominio" else "Informação")
            ao_mudar_tipo_registro()  # Atualiza visibilidade do label informativo
            
            entrada_secao.delete(0, tk.END)
            entrada_secao.insert(0, dominio.get("secao", "Inclusão Manual"))
            
            # Limpa a grid atual
            for item in tree_grid.get_children():
                tree_grid.delete(item)
            
            # Preenche a grid com as opções existentes
            opcoes = dominio.get("opcoes", [])
            for opcao in opcoes:
                tree_grid.insert("", tk.END, values=(opcao.get("valor", ""), opcao.get("descricao", "")))
            # Não mostra mensagem de sucesso, apenas limpa o status
            label_status.config(text="")
            
        except Exception as e:
            atualizar_status(f"Erro ao buscar domínio: {str(e)}", "red")
    
    ttk.Button(frame_campos, text="Buscar", command=buscar_dominio).grid(row=0, column=2, padx=5, pady=5)
    
    # Atalho: pressionar Enter no campo Tag também aciona a busca
    entrada_tag.bind('<Return>', lambda e: buscar_dominio())
    
    ttk.Label(frame_campos, text="Descrição Tag:*").grid(row=1, column=0, sticky='w', padx=5, pady=5)
    entrada_descricao_tag = ttk.Entry(frame_campos, width=30)
    entrada_descricao_tag.grid(row=1, column=1, padx=5, pady=5)
    
    ttk.Label(frame_campos, text="Tipo registro:*").grid(row=2, column=0, sticky='w', padx=5, pady=5)
    tipo_registro_var = tk.StringVar(value="Domínio")
    combo_tipo_registro = ttk.Combobox(frame_campos, textvariable=tipo_registro_var, 
                                       values=["Domínio", "Informação"], 
                                       state="readonly", width=27)
    combo_tipo_registro.grid(row=2, column=1, padx=5, pady=5)
    
    # Label informativo que aparece quando tipo é "Informação"
    label_info_tipo = tk.Label(frame_campos, 
                              text="💡 Informação: o campo 'Valor' será preenchido automaticamente com 'Info'.\n" +
                                   "Use este tipo para adicionar dicas que aparecerão como tooltips no XML.",
                              bg=cores["bg"], 
                              fg="#2874A6",
                              font=(fonts["family"], fonts["size_small"], "italic"),
                              justify=tk.LEFT,
                              wraplength=500)
    label_info_tipo.grid(row=2, column=2, columnspan=2, sticky='w', padx=10, pady=5)
    label_info_tipo.grid_remove()  # Oculta inicialmente
    
    # Campo Seção (será ocultado se tipo = Informação)
    label_secao = ttk.Label(frame_campos, text="Seção:")
    label_secao.grid(row=3, column=0, sticky='w', padx=5, pady=5)
    entrada_secao = ttk.Entry(frame_campos, width=30)
    entrada_secao.insert(0, "Inclusão Manual") 
    entrada_secao.grid(row=3, column=1, padx=5, pady=5)
    
    def ao_mudar_tipo_registro(event=None):
        """Mostra/oculta informações e campo Seção quando o tipo registro muda"""
        if tipo_registro_var.get() == "Informação":
            label_info_tipo.grid()
            # Oculta campo Seção para tipo Informação
            label_secao.grid_remove()
            entrada_secao.grid_remove()
        else:
            label_info_tipo.grid_remove()
            # Mostra campo Seção para tipo Domínio
            label_secao.grid()
            entrada_secao.grid()
    
    combo_tipo_registro.bind('<<ComboboxSelected>>', ao_mudar_tipo_registro)
    
    # Frame Grid - área com Treeview estilo Excel (LINHA 2 - EXPANSÍVEL)
    frame_grid = ttk.Frame(janela_dominios, padding=10)
    frame_grid.grid(row=2, column=0, sticky='nsew')
    
    # Frame com instrução e ícone
    frame_instrucao = tk.Frame(frame_grid, bg=cores["bg"])
    frame_instrucao.pack(anchor='w', fill='x', pady=(0, 5))
    
    tk.Label(frame_instrucao, text="💡", bg=cores["bg"],
            font=(fonts["family"], fonts["size_medium"])).pack(side=tk.LEFT, padx=(0, spacing["sm"]))
    
    tk.Label(frame_instrucao,
             text="Opções do Domínio:* Dê duplo clique na célula para editar diretamente | Tab para avançar",
             bg=cores["bg"], fg=cores["fg_secondary"],
             font=(fonts["family"], fonts["size_small"], "italic")).pack(side=tk.LEFT, anchor='w')
    
    # Container com borda para o Treeview
    tree_container = tk.Frame(frame_grid, relief=tk.SOLID, borderwidth=1, bg=cores["border"])
    tree_container.pack(fill=tk.BOTH, expand=True)
    
    # Scrollbar
    scrollbar_tree = ttk.Scrollbar(tree_container, orient=tk.VERTICAL)
    scrollbar_tree.pack(side=tk.RIGHT, fill=tk.Y)
    
    # Treeview estilo Excel
    tree_grid = ttk.Treeview(tree_container, columns=("valor", "descricao"),
                             show="headings", yscrollcommand=scrollbar_tree.set,
                             selectmode="extended", height=10)
    
    tree_grid.heading("valor", text="Valor")
    tree_grid.heading("descricao", text="Descrição")
    tree_grid.column("valor", width=120, anchor="w")
    tree_grid.column("descricao", width=450, anchor="w")
    tree_grid.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    
    scrollbar_tree.config(command=tree_grid.yview)
    
    # Configura tags para cores alternadas (estilo Excel)
    tree_grid.tag_configure('oddrow', background=cores["text_bg"])
    tree_grid.tag_configure('evenrow', background=cores["bg_hover"])
    tree_grid.tag_configure('editing', background=cores["tag_amarelo"])
    
    # Variável para controlar edição inline
    entry_edicao = None
    item_editando = None
    coluna_editando = None
    
    def adicionar_linha_grid():
        """Adiciona uma nova linha vazia na grid"""
        total_linhas = len(tree_grid.get_children())
        tag = 'evenrow' if total_linhas % 2 else 'oddrow'
        
        # Verifica o tipo registro selecionado
        tipo_selecionado = tipo_registro_var.get()
        
        if tipo_selecionado == "Informação":
            # Para informação, preenche valor automaticamente com "Info"
            novo_item = tree_grid.insert("", tk.END, values=("Info", ""), tags=(tag,))
        else:
            # Para domínio, cria linha vazia
            novo_item = tree_grid.insert("", tk.END, values=("", ""), tags=(tag,))
        
        # Reaplica cores alternadas
        for i, item in enumerate(tree_grid.get_children()):
            tag = 'evenrow' if i % 2 else 'oddrow'
            tree_grid.item(item, tags=(tag,))
        
        # Seleciona o novo item
        tree_grid.selection_set(novo_item)
        tree_grid.focus(novo_item)
        
        # Inicia edição: se for Informação, vai direto para descrição
        if tipo_selecionado == "Informação":
            iniciar_edicao_inline(novo_item, "descricao")
        else:
            iniciar_edicao_inline(novo_item, "valor")
    
    def iniciar_edicao_inline(item, coluna):
        """Inicia a edição inline de uma célula"""
        nonlocal entry_edicao, item_editando, coluna_editando
        
        # Cancela edição anterior se existir
        cancelar_edicao_inline()
        
        # Verifica se é tipo Informação e está tentando editar o valor
        tipo_selecionado = tipo_registro_var.get()
        valores_item = tree_grid.item(item)['values']
        
        if tipo_selecionado == "Informação" and coluna == "valor":
            # Não permite editar o campo valor quando é Informação
            # Garante que o valor seja "Info"
            if valores_item[0] != "Info":
                tree_grid.item(item, values=("Info", valores_item[1] if len(valores_item) > 1 else ""))
            return
        
        # Pega a posição e tamanho da célula
        bbox = tree_grid.bbox(item, column=coluna)
        if not bbox:
            return
        
        x, y, width, height = bbox
        
        # Pega o valor atual
        valores = tree_grid.item(item)['values']
        valor_atual = valores[0] if coluna == "valor" else valores[1]
        
        # Cria Entry para edição
        entry_edicao = tk.Entry(tree_grid,
                               bg=cores["tag_amarelo"],
                               fg=cores["text_fg"],
                               font=(fonts["family"], fonts["size_normal"]),
                               relief=tk.FLAT,
                               borderwidth=1,
                               highlightthickness=2,
                               highlightbackground=cores["entry_focus"],
                               highlightcolor=cores["entry_focus"])
        entry_edicao.place(x=x, y=y, width=width, height=height)
        entry_edicao.insert(0, valor_atual)
        entry_edicao.select_range(0, tk.END)
        entry_edicao.focus()
        
        item_editando = item
        coluna_editando = coluna
        
        # Marca o item como em edição
        tree_grid.item(item, tags=('editing',))
        
        # Bindings
        entry_edicao.bind('<Return>', lambda e: salvar_edicao_inline())
        entry_edicao.bind('<Tab>', lambda e: salvar_e_proxima_coluna())
        entry_edicao.bind('<Escape>', lambda e: cancelar_edicao_inline())
        entry_edicao.bind('<FocusOut>', lambda e: salvar_edicao_inline())
    
    def salvar_edicao_inline():
        """Salva a edição inline"""
        nonlocal entry_edicao, item_editando, coluna_editando
        
        if not entry_edicao or not item_editando:
            return
        
        # Pega o novo valor
        novo_valor = entry_edicao.get().strip()
        
        # Pega os valores atuais
        valores = list(tree_grid.item(item_editando)['values'])
        
        # Atualiza o valor da coluna editada
        if coluna_editando == "valor":
            valores[0] = novo_valor
        else:
            valores[1] = novo_valor
        
        # Atualiza o item
        tree_grid.item(item_editando, values=tuple(valores))
        
        # Restaura a cor original
        idx = tree_grid.index(item_editando)
        tag = 'evenrow' if idx % 2 else 'oddrow'
        tree_grid.item(item_editando, tags=(tag,))
        
        # Limpa a edição
        entry_edicao.destroy()
        entry_edicao = None
        item_editando = None
        coluna_editando = None
    
    def salvar_e_proxima_coluna():
        """Salva e move para a próxima coluna"""
        nonlocal coluna_editando, item_editando
        
        if coluna_editando == "valor":
            # Salva e vai para descrição
            item_atual = item_editando
            salvar_edicao_inline()
            iniciar_edicao_inline(item_atual, "descricao")
        else:
            # Salva e sai da edição
            salvar_edicao_inline()
        
        return "break"  # Previne comportamento padrão do Tab
    
    def cancelar_edicao_inline():
        """Cancela a edição inline"""
        nonlocal entry_edicao, item_editando, coluna_editando
        
        if entry_edicao:
            entry_edicao.destroy()
            entry_edicao = None
        
        if item_editando:
            # Restaura a cor original
            idx = tree_grid.index(item_editando)
            tag = 'evenrow' if idx % 2 else 'oddrow'
            tree_grid.item(item_editando, tags=(tag,))
            item_editando = None
            coluna_editando = None
    
    def editar_linha_selecionada():
        """Inicia edição da linha selecionada"""
        selecionadas = tree_grid.selection()
        if not selecionadas:
            atualizar_status("Selecione uma linha para editar.", "orange")
            return
        
        # Inicia edição na primeira coluna
        iniciar_edicao_inline(selecionadas[0], "valor")
    
    # Duplo clique para editar a célula clicada
    def ao_duplo_clique(event):
        item = tree_grid.identify_row(event.y)
        coluna = tree_grid.identify_column(event.x)
        
        if item and coluna:
            # Mapeia a coluna (#1, #2) para o nome interno
            coluna_nome = "valor" if coluna == "#1" else "descricao"
            iniciar_edicao_inline(item, coluna_nome)
    
    tree_grid.bind('<Double-1>', ao_duplo_clique)
    
    def remover_linhas_selecionadas():
        """Remove as linhas selecionadas"""
        selecionadas = tree_grid.selection()
        
        if not selecionadas:
            atualizar_status("Nenhuma linha selecionada para remover.", "orange")
            return
        
        for item in selecionadas:
            tree_grid.delete(item)
        
        # Reaplica cores alternadas
        for i, item in enumerate(tree_grid.get_children()):
            tag = 'evenrow' if i % 2 else 'oddrow'
            tree_grid.item(item, tags=(tag,))
        
        atualizar_status(f"{len(selecionadas)} linha(s) removida(s) com sucesso.", "green")
    
    # Frame para botões da grid - fixo na parte inferior (LINHA 3 - FIXO)
    frame_botoes_grid = ttk.Frame(janela_dominios, padding=10)
    frame_botoes_grid.grid(row=3, column=0, sticky='ew')
    
    ttk.Button(frame_botoes_grid, text="➕ Adicionar Linha", command=adicionar_linha_grid).pack(side=tk.LEFT, padx=5)
    ttk.Button(frame_botoes_grid, text="✏️ Editar Linha", 
              command=editar_linha_selecionada).pack(side=tk.LEFT, padx=5)
    ttk.Button(frame_botoes_grid, text="🗑️ Remover Linhas", command=remover_linhas_selecionadas,
              style="Secondary.TButton").pack(side=tk.LEFT, padx=5)
    
    # Frame inferior - botão salvar - fixo na parte inferior (LINHA 4 - FIXO)
    frame_inferior = ttk.Frame(janela_dominios, padding=10)
    frame_inferior.grid(row=4, column=0, sticky='ew')
    
    def salvar_dominio():
        """Salva o domínio no arquivo JSON"""
        nome_tag = entrada_tag.get().strip()
        descricao_tag = entrada_descricao_tag.get().strip()
        secao = entrada_secao.get().strip()
        tipo_registro = tipo_registro_var.get()
        
        # Validações
        if not nome_tag:
            atualizar_status("O campo 'Tag' é obrigatório.", "red")
            entrada_tag.focus()
            return
        
        if not descricao_tag:
            atualizar_status("O campo 'Descrição Tag' é obrigatório.", "red")
            entrada_descricao_tag.focus()
            return
        
        # Coleta dados da grid (Treeview)
        opcoes = []
        for item in tree_grid.get_children():
            valores = tree_grid.item(item)['values']
            if valores and len(valores) >= 2:
                valor = str(valores[0]).strip()
                descricao = str(valores[1]).strip()
                if valor and descricao:
                    opcoes.append({
                        "valor": valor,
                        "descricao": descricao
                    })
        
        if not opcoes:
            atualizar_status("É obrigatório informar pelo menos uma opção com valor e descrição.", "red")
            return
        
        # Validação específica para tipo Informação
        if tipo_registro == "Informação":
            # Verifica se todas as opções têm valor = "Info"
            for opcao in opcoes:
                if opcao["valor"] != "Info":
                    atualizar_status("Para tipo 'Informação', o valor deve ser 'Info'.", "red")
                    return
        
        # Define seção padrão se não informada
        if not secao:
            secao = "Inclusão Manual"
        
        # Obtém caminho do arquivo
        json_path = config_manager.obter_caminho_arquivo("dominios_DDA.json")
        if not json_path:
            atualizar_status("Operação cancelada.", "orange")
            return
        
        # Carrega JSON existente
        try:
            if os.path.exists(json_path):
                with open(json_path, "r", encoding="utf-8") as f:
                    dominios = json.load(f)
            else:
                dominios = {}
            
            # Verifica se é inclusão ou atualização
            ja_existia = nome_tag in dominios
            acao = "atualizado" if ja_existia else "salvo"
            
            # Define o tipo (converte para minúsculo para o JSON)
            tipo = "informacao" if tipo_registro == "Informação" else "dominio"
            
            # Adiciona ou atualiza domínio
            dominios[nome_tag] = {
                "tipo": tipo,
                "secao": secao,
                "tag": descricao_tag,
                "opcoes": opcoes
            }
            
            # Salva JSON
            with open(json_path, "w", encoding="utf-8") as f:
                json.dump(dominios, f, indent=4, ensure_ascii=False)
            
            # Recarrega os domínios no parser
            parser.DOMINIOS = dominios
            
            tipo_msg = "Informação" if tipo == "informacao" else "Domínio"
            atualizar_status(f"{tipo_msg} '{nome_tag}' {acao} em: {json_path}", "green")
            
        except Exception as e:
            atualizar_status(f"Erro ao salvar domínio: {str(e)}", "red")
    
    ttk.Button(frame_inferior, text="Salvar", command=salvar_dominio).pack(side=tk.RIGHT, padx=5)
    ttk.Button(frame_inferior, text="Fechar", command=janela_dominios.destroy).pack(side=tk.RIGHT, padx=5)

def abrir_buscar_substituir():
    """Abre janela de buscar e substituir com Ctrl+F - Design Moderno"""
    janela_buscar = tk.Toplevel(janela)
    janela_buscar.title("Buscar e Substituir")
    janela_buscar.geometry("550x240")
    janela_buscar.minsize(550, 240)
    janela_buscar.resizable(False, False)
    
    cores = gerenciador_temas.get_cores()
    fonts = gerenciador_temas.get_font_config()
    spacing = gerenciador_temas.get_spacing_config()
    janela_buscar.configure(bg=cores["bg"])
    
    # Variável para controlar a posição da última busca
    janela_buscar.ultima_posicao = "1.0"
    janela_buscar.total_encontrados = 0
    
    # Frame principal
    frame_principal = tk.Frame(janela_buscar, bg=cores["bg"])
    frame_principal.pack(fill=tk.BOTH, expand=True, padx=spacing["xl"], pady=spacing["lg"])
    
    # Título
    tk.Label(frame_principal, 
             text="🔍 Buscar e Substituir",
             bg=cores["bg"],
             fg=cores["fg"],
             font=(fonts["family"], fonts["size_large"], "bold")).grid(row=0, column=0, columnspan=3, 
                                                                       sticky='w', pady=(0, spacing["lg"]))
    
    # Campo Buscar com label moderna
    tk.Label(frame_principal, 
             text="Buscar:",
             bg=cores["bg"],
             fg=cores["fg"],
             font=(fonts["family"], fonts["size_normal"], "bold")).grid(row=1, column=0, sticky='w', pady=spacing["sm"])
    
    entrada_buscar = tk.Entry(frame_principal, 
                             width=45,
                             bg=cores["entry_bg"],
                             fg=cores["text_fg"],
                             font=(fonts["family"], fonts["size_normal"]),
                             relief=tk.FLAT,
                             borderwidth=1,
                             highlightthickness=2,
                             highlightbackground=cores["entry_border"],
                             highlightcolor=cores["entry_focus"])
    entrada_buscar.grid(row=1, column=1, columnspan=2, sticky='ew', padx=(spacing["md"], 0), pady=spacing["sm"])
    entrada_buscar.focus()
    
    # Campo Substituir
    tk.Label(frame_principal,
             text="Substituir:",
             bg=cores["bg"],
             fg=cores["fg"],
             font=(fonts["family"], fonts["size_normal"], "bold")).grid(row=2, column=0, sticky='w', pady=spacing["sm"])
    
    entrada_substituir = tk.Entry(frame_principal,
                                  width=45,
                                  bg=cores["entry_bg"],
                                  fg=cores["text_fg"],
                                  font=(fonts["family"], fonts["size_normal"]),
                                  relief=tk.FLAT,
                                  borderwidth=1,
                                  highlightthickness=2,
                                  highlightbackground=cores["entry_border"],
                                  highlightcolor=cores["entry_focus"])
    entrada_substituir.grid(row=2, column=1, columnspan=2, sticky='ew', padx=(spacing["md"], 0), pady=spacing["sm"])
    
    # Configurar peso das colunas
    frame_principal.columnconfigure(1, weight=1)
    
    # Label de status no rodapé
    label_status = tk.Label(frame_principal,
                           text="",
                           fg=cores["info"],
                           bg=cores["bg"],
                           font=(fonts["family"], fonts["size_small"]))
    label_status.grid(row=4, column=0, columnspan=3, pady=(spacing["md"], 0), sticky='w')
    
    def atualizar_status(mensagem):
        """Atualiza a mensagem de status no rodapé"""
        label_status.config(text=mensagem)
    
    def remover_destaques():
        """Remove todos os destaques de busca"""
        campo_resultado.tag_remove("busca_destaque", "1.0", tk.END)
    
    def buscar():
        """Busca e destaca todas as ocorrências no texto"""
        texto_buscar = entrada_buscar.get()
        
        if not texto_buscar:
            atualizar_status("Digite algo no campo 'Buscar'.")
            return
        
        # Remove destaques anteriores
        remover_destaques()
        
        # Configura a tag de destaque
        campo_resultado.tag_config("busca_destaque", background=cores["tag_amarelo"], foreground=cores["text_fg"])
        
        # Busca todas as ocorrências
        inicio = "1.0"
        contador = 0
        primeira_posicao = None
        
        while True:
            pos = campo_resultado.search(texto_buscar, inicio, stopindex=tk.END, nocase=True)
            if not pos:
                break
            
            if primeira_posicao is None:
                primeira_posicao = pos
            
            # Calcula a posição final
            fim = f"{pos}+{len(texto_buscar)}c"
            
            # Adiciona o destaque
            campo_resultado.tag_add("busca_destaque", pos, fim)
            
            contador += 1
            inicio = fim
        
        # Atualiza variáveis de controle
        janela_buscar.total_encontrados = contador
        janela_buscar.ultima_posicao = primeira_posicao if primeira_posicao else "1.0"
        
        # Exibe mensagem no rodapé
        if contador == 0:
            atualizar_status("✗ 0 ocorrências encontradas.")
        else:
            # Move o scroll para a primeira ocorrência
            campo_resultado.see(primeira_posicao)
            atualizar_status(f"✓ {contador} ocorrência(s) encontrada(s).")
    
    def substituir():
        """Substitui a próxima ocorrência encontrada"""
        texto_buscar = entrada_buscar.get()
        texto_substituir = entrada_substituir.get()
        
        if not texto_buscar:
            atualizar_status("Digite algo no campo 'Buscar'.")
            return
        
        # Busca a próxima ocorrência a partir da última posição
        pos = campo_resultado.search(texto_buscar, janela_buscar.ultima_posicao, stopindex=tk.END, nocase=True)
        
        if not pos:
            # Se não encontrou, tenta do início
            pos = campo_resultado.search(texto_buscar, "1.0", stopindex=tk.END, nocase=True)
            
            if not pos:
                atualizar_status("✗ Nenhuma ocorrência encontrada.")
                remover_destaques()
                return
        
        # Calcula a posição final
        fim = f"{pos}+{len(texto_buscar)}c"
        
        # Substitui o texto
        campo_resultado.delete(pos, fim)
        campo_resultado.insert(pos, texto_substituir)
        
        # Atualiza a posição para a próxima busca
        janela_buscar.ultima_posicao = f"{pos}+{len(texto_substituir)}c"
        
        # Move o scroll para a posição substituída
        campo_resultado.see(pos)
        
        # Marca como selecionado temporariamente
        campo_resultado.tag_remove("sel", "1.0", tk.END)
        campo_resultado.tag_add("sel", pos, janela_buscar.ultima_posicao)
        
        # Atualiza números de linha
        if atualizar_numeros_linha_func:
            atualizar_numeros_linha_func()
        
        # Reaplica formatações
        aplicar_formatacao_tags_especificas()
        
        atualizar_status("✓ 1 ocorrência substituída.")
    
    def substituir_todos():
        """Substitui todas as ocorrências encontradas"""
        texto_buscar = entrada_buscar.get()
        texto_substituir = entrada_substituir.get()
        
        if not texto_buscar:
            atualizar_status("Digite algo no campo 'Buscar'.")
            return
        
        # Conta quantas vezes vai substituir
        inicio = "1.0"
        contador = 0
        
        while True:
            pos = campo_resultado.search(texto_buscar, inicio, stopindex=tk.END, nocase=True)
            if not pos:
                break
            contador += 1
            inicio = f"{pos}+1c"
        
        if contador == 0:
            atualizar_status("✗ Nenhuma ocorrência encontrada.")
            return
        
        # Substitui todas as ocorrências (do fim para o início para não alterar índices)
        while True:
            pos = campo_resultado.search(texto_buscar, "1.0", stopindex=tk.END, nocase=True)
            if not pos:
                break
            
            fim = f"{pos}+{len(texto_buscar)}c"
            campo_resultado.delete(pos, fim)
            campo_resultado.insert(pos, texto_substituir)
        
        # Remove destaques
        remover_destaques()
        
        # Atualiza números de linha
        if atualizar_numeros_linha_func:
            atualizar_numeros_linha_func()
        
        # Reaplica formatações
        aplicar_formatacao_tags_especificas()
        
        atualizar_status(f"✓ {contador} ocorrência(s) substituída(s).")
    
    # Frame para botões com estilo moderno
    frame_botoes = tk.Frame(frame_principal, bg=cores["bg"])
    frame_botoes.grid(row=3, column=0, columnspan=3, pady=(spacing["lg"], 0))
    
    # Cria botões estilizados com ttk
    ttk.Button(frame_botoes, text="Buscar", command=buscar, width=15).pack(side=tk.LEFT, padx=spacing["sm"])
    ttk.Button(frame_botoes, text="Substituir", command=substituir, width=15, 
               style="Secondary.TButton").pack(side=tk.LEFT, padx=spacing["sm"])
    ttk.Button(frame_botoes, text="Substituir Todos", command=substituir_todos, width=15,
               style="Secondary.TButton").pack(side=tk.LEFT, padx=spacing["sm"])
    
    # Permite buscar com Enter no campo buscar
    entrada_buscar.bind('<Return>', lambda e: buscar())
    
    # Ao fechar a janela, remove os destaques
    janela_buscar.protocol("WM_DELETE_WINDOW", lambda: (remover_destaques(), janela_buscar.destroy()))

def abrir_tela_filas_mq():
    """Abre a tela para gerenciamento de filas IBMMQ"""
    janela_filas = tk.Toplevel(janela)
    janela_filas.title("Gerenciamento de Filas MQ")
    
    largura = 900
    altura = 600
    largura_tela = janela.winfo_screenwidth()
    altura_tela = janela.winfo_screenheight()
    x = (largura_tela // 2) - (largura // 2)
    y = (altura_tela // 2) - (altura // 2)
    janela_filas.geometry(f"{largura}x{altura}+{x}+{y}")
    janela_filas.minsize(800, 500)
    
    # Obtém configurações de tema
    cores = gerenciador_temas.get_cores()
    fonts = gerenciador_temas.get_font_config()
    spacing = gerenciador_temas.get_spacing_config()
    janela_filas.configure(bg=cores["bg"])
    
    # Configura o grid da janela principal
    janela_filas.columnconfigure(0, weight=1)
    janela_filas.rowconfigure(0, weight=0)  # Label status - fixo
    janela_filas.rowconfigure(1, weight=0)  # Frame campos - fixo
    janela_filas.rowconfigure(2, weight=1)  # Frame grid - expansível
    janela_filas.rowconfigure(3, weight=0)  # Frame botões - fixo
    
    # Label de Status (LINHA 0)
    label_status = ttk.Label(janela_filas, text="", font=("Arial", 9), foreground="blue")
    label_status.grid(row=0, column=0, sticky='ew', padx=10, pady=(5, 0))
    
    def atualizar_status(mensagem, cor="blue"):
        """Atualiza a mensagem de status"""
        label_status.config(text=mensagem, foreground=cor)
        janela_filas.after(5000, lambda: label_status.config(text=""))
    
    # Frame superior - campos de entrada (LINHA 1)
    frame_campos = ttk.Frame(janela_filas, padding=10)
    frame_campos.grid(row=1, column=0, sticky='ew')
    
    # Configurar colunas para expandir
    frame_campos.columnconfigure(1, weight=1)
    frame_campos.columnconfigure(3, weight=1)
    frame_campos.columnconfigure(5, weight=1)
    
    # Linha 1: Nome do Ambiente e Gerenciador
    ttk.Label(frame_campos, text="Nome do Ambiente:*").grid(row=0, column=0, sticky='w', padx=5, pady=5)
    entrada_ambiente = ttk.Entry(frame_campos, width=30)
    entrada_ambiente.grid(row=0, column=1, padx=5, pady=5, sticky='ew')
    
    ttk.Label(frame_campos, text="Gerenciador:*").grid(row=0, column=2, sticky='w', padx=5, pady=5)
    entrada_gerenciador = ttk.Entry(frame_campos, width=30)
    entrada_gerenciador.grid(row=0, column=3, padx=5, pady=5, sticky='ew')
    
    # Linha 2: Canal e Host
    ttk.Label(frame_campos, text="Canal:*").grid(row=1, column=0, sticky='w', padx=5, pady=5)
    entrada_canal = ttk.Entry(frame_campos, width=30)
    entrada_canal.grid(row=1, column=1, padx=5, pady=5, sticky='ew')
    
    ttk.Label(frame_campos, text="Host:*").grid(row=1, column=2, sticky='w', padx=5, pady=5)
    entrada_host = ttk.Entry(frame_campos, width=30)
    entrada_host.grid(row=1, column=3, padx=5, pady=5, sticky='ew')
    
    # Linha 3: Porta e Nome da Fila
    ttk.Label(frame_campos, text="Porta:*").grid(row=2, column=0, sticky='w', padx=5, pady=5)
    entrada_porta = ttk.Entry(frame_campos, width=30)
    entrada_porta.grid(row=2, column=1, padx=5, pady=5, sticky='ew')
    
    ttk.Label(frame_campos, text="Nome da Fila:*").grid(row=2, column=2, sticky='w', padx=5, pady=5)
    entrada_fila = ttk.Entry(frame_campos, width=30)
    entrada_fila.grid(row=2, column=3, padx=5, pady=5, sticky='ew')
    
    # Frame Grid - área com Treeview (LINHA 2)
    frame_grid = ttk.Frame(janela_filas, padding=10)
    frame_grid.grid(row=2, column=0, sticky='nsew', padx=10)
    
    # Container com borda para o Treeview
    tree_container = tk.Frame(frame_grid, relief=tk.SOLID, borderwidth=1, bg=cores["border"])
    tree_container.pack(fill=tk.BOTH, expand=True)
    
    # Scrollbar
    scrollbar_tree = ttk.Scrollbar(tree_container, orient=tk.VERTICAL)
    scrollbar_tree.pack(side=tk.RIGHT, fill=tk.Y)
    
    # Treeview
    colunas = ("ambiente", "gerenciador", "canal", "host", "porta", "fila")
    tree_grid = ttk.Treeview(tree_container, columns=colunas,
                             show="headings", yscrollcommand=scrollbar_tree.set,
                             selectmode="extended", height=12)
    
    tree_grid.heading("ambiente", text="Nome do Ambiente")
    tree_grid.heading("gerenciador", text="Gerenciador")
    tree_grid.heading("canal", text="Canal")
    tree_grid.heading("host", text="Host")
    tree_grid.heading("porta", text="Porta")
    tree_grid.heading("fila", text="Nome da Fila")
    
    tree_grid.column("ambiente", width=150, anchor="w")
    tree_grid.column("gerenciador", width=120, anchor="w")
    tree_grid.column("canal", width=120, anchor="w")
    tree_grid.column("host", width=150, anchor="w")
    tree_grid.column("porta", width=80, anchor="w")
    tree_grid.column("fila", width=150, anchor="w")
    
    tree_grid.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    scrollbar_tree.config(command=tree_grid.yview)
    
    # Configura tags para cores alternadas
    tree_grid.tag_configure('oddrow', background=cores["text_bg"])
    tree_grid.tag_configure('evenrow', background=cores["bg_hover"])
    
    def carregar_filas():
        """Carrega as filas do arquivo JSON"""
        json_path = config_manager.obter_diretorio_config()
        if json_path:
            json_path = os.path.join(json_path, "filas_mq.json")
        else:
            json_path = None
        
        if json_path and os.path.exists(json_path):
            try:
                with open(json_path, "r", encoding="utf-8") as f:
                    filas = json.load(f)
                    
                # Limpa a grid
                for item in tree_grid.get_children():
                    tree_grid.delete(item)
                
                # Preenche a grid
                for i, fila in enumerate(filas):
                    tag = 'evenrow' if i % 2 else 'oddrow'
                    tree_grid.insert("", tk.END, values=(
                        fila.get("ambiente", ""),
                        fila.get("gerenciador", ""),
                        fila.get("canal", ""),
                        fila.get("host", ""),
                        fila.get("porta", ""),
                        fila.get("fila", "")
                    ), tags=(tag,))
            except Exception as e:
                atualizar_status(f"Erro ao carregar filas: {str(e)}", "red")
    
    def salvar_filas():
        """Salva as filas no arquivo JSON"""
        json_path = config_manager.obter_caminho_arquivo("filas_mq.json")
        if not json_path:
            atualizar_status("Operação cancelada.", "orange")
            return
        
        try:
            filas = []
            for item in tree_grid.get_children():
                valores = tree_grid.item(item)['values']
                filas.append({
                    "ambiente": valores[0],
                    "gerenciador": valores[1],
                    "canal": valores[2],
                    "host": valores[3],
                    "porta": valores[4],
                    "fila": valores[5]
                })
            
            with open(json_path, "w", encoding="utf-8") as f:
                json.dump(filas, f, indent=2, ensure_ascii=False)
            
            atualizar_status(f"Filas salvas em: {json_path}", "green")
        except Exception as e:
            atualizar_status(f"Erro ao salvar filas: {str(e)}", "red")
    
    def adicionar_linha():
        """Adiciona uma nova linha na grid com os dados dos campos"""
        # Validação
        if not entrada_ambiente.get().strip():
            atualizar_status("Nome do Ambiente é obrigatório.", "red")
            entrada_ambiente.focus()
            return
        if not entrada_gerenciador.get().strip():
            atualizar_status("Gerenciador é obrigatório.", "red")
            entrada_gerenciador.focus()
            return
        if not entrada_canal.get().strip():
            atualizar_status("Canal é obrigatório.", "red")
            entrada_canal.focus()
            return
        if not entrada_host.get().strip():
            atualizar_status("Host é obrigatório.", "red")
            entrada_host.focus()
            return
        if not entrada_porta.get().strip():
            atualizar_status("Porta é obrigatória.", "red")
            entrada_porta.focus()
            return
        if not entrada_fila.get().strip():
            atualizar_status("Nome da Fila é obrigatório.", "red")
            entrada_fila.focus()
            return
        
        # Adiciona na grid
        total_linhas = len(tree_grid.get_children())
        tag = 'evenrow' if total_linhas % 2 else 'oddrow'
        tree_grid.insert("", tk.END, values=(
            entrada_ambiente.get().strip(),
            entrada_gerenciador.get().strip(),
            entrada_canal.get().strip(),
            entrada_host.get().strip(),
            entrada_porta.get().strip(),
            entrada_fila.get().strip()
        ), tags=(tag,))
        
        # Limpa os campos
        entrada_ambiente.delete(0, tk.END)
        entrada_gerenciador.delete(0, tk.END)
        entrada_canal.delete(0, tk.END)
        entrada_host.delete(0, tk.END)
        entrada_porta.delete(0, tk.END)
        entrada_fila.delete(0, tk.END)
        
        # Reaplica cores alternadas
        for i, item in enumerate(tree_grid.get_children()):
            tag = 'evenrow' if i % 2 else 'oddrow'
            tree_grid.item(item, tags=(tag,))
        
        atualizar_status("Linha adicionada com sucesso!", "green")
        entrada_ambiente.focus()
    
    def editar_linha():
        """Carrega os dados da linha selecionada nos campos para edição"""
        selecionados = tree_grid.selection()
        if not selecionados:
            atualizar_status("Selecione uma linha para editar.", "orange")
            return
        
        if len(selecionados) > 1:
            atualizar_status("Selecione apenas uma linha para editar.", "orange")
            return
        
        item = selecionados[0]
        valores = tree_grid.item(item)['values']
        
        # Preenche os campos
        entrada_ambiente.delete(0, tk.END)
        entrada_ambiente.insert(0, valores[0])
        
        entrada_gerenciador.delete(0, tk.END)
        entrada_gerenciador.insert(0, valores[1])
        
        entrada_canal.delete(0, tk.END)
        entrada_canal.insert(0, valores[2])
        
        entrada_host.delete(0, tk.END)
        entrada_host.insert(0, valores[3])
        
        entrada_porta.delete(0, tk.END)
        entrada_porta.insert(0, valores[4])
        
        entrada_fila.delete(0, tk.END)
        entrada_fila.insert(0, valores[5])
        
        # Remove a linha da grid
        tree_grid.delete(item)
        
        # Reaplica cores alternadas
        for i, item in enumerate(tree_grid.get_children()):
            tag = 'evenrow' if i % 2 else 'oddrow'
            tree_grid.item(item, tags=(tag,))
        
        atualizar_status("Edite os campos e clique em 'Adicionar Linha' para salvar.", "blue")
        entrada_ambiente.focus()
    
    def remover_linhas():
        """Remove as linhas selecionadas da grid"""
        selecionados = tree_grid.selection()
        if not selecionados:
            atualizar_status("Selecione pelo menos uma linha para remover.", "orange")
            return
        
        for item in selecionados:
            tree_grid.delete(item)
        
        # Reaplica cores alternadas
        for i, item in enumerate(tree_grid.get_children()):
            tag = 'evenrow' if i % 2 else 'oddrow'
            tree_grid.item(item, tags=(tag,))
        
        atualizar_status(f"{len(selecionados)} linha(s) removida(s).", "green")
    
    # Frame de botões (LINHA 3)
    frame_botoes = ttk.Frame(janela_filas, padding=10)
    frame_botoes.grid(row=3, column=0, sticky='ew')
    
    ttk.Button(frame_botoes, text="Adicionar Linha", command=adicionar_linha).pack(side=tk.LEFT, padx=5)
    ttk.Button(frame_botoes, text="Editar Linha", command=editar_linha).pack(side=tk.LEFT, padx=5)
    ttk.Button(frame_botoes, text="Remover Linhas", command=remover_linhas).pack(side=tk.LEFT, padx=5)
    ttk.Button(frame_botoes, text="Salvar", command=salvar_filas).pack(side=tk.LEFT, padx=5)
    ttk.Button(frame_botoes, text="Fechar", command=janela_filas.destroy).pack(side=tk.RIGHT, padx=5)
    
    # Carrega as filas existentes
    carregar_filas()
    
    # Foco inicial
    entrada_ambiente.focus()

def abrir_tela_configuracoes():
    """Abre a tela de configurações do sistema"""
    try:
        # Obtém configurações de cores
        cores = gerenciador_temas.get_cores()
        fonts = gerenciador_temas.get_font_config()
        spacing = gerenciador_temas.get_spacing_config()
        
        janela_config = tk.Toplevel(janela)
        janela_config.title("Configurações do Sistema")
        janela_config.geometry("700x300")
        janela_config.resizable(False, False)
        janela_config.configure(bg=cores["bg"])
        
        # Centraliza a janela
        janela_config.transient(janela)
        janela_config.grab_set()
        
        # Frame principal
        frame_principal = tk.Frame(janela_config, bg=cores["bg"], padx=20, pady=20)
        frame_principal.pack(fill=tk.BOTH, expand=True)
        
        print("DEBUG: Frame principal criado")
    except Exception as e:
        print(f"ERRO ao criar janela de configurações: {e}")
        import traceback
        traceback.print_exc()
        return
    
    try:
        # Título
        titulo = tk.Label(
            frame_principal,
            text="Configurações",
            font=(fonts["family"], fonts["size_large"], "bold"),
            bg=cores["bg"],
            fg=cores["label_accent"]
        )
        titulo.pack(pady=(0, 20))
        print("DEBUG: Título criado")
        
        # Frame para o diretório
        frame_dir = tk.Frame(frame_principal, bg=cores["bg"])
        frame_dir.pack(fill=tk.X, pady=10)
        
        label_dir = tk.Label(
            frame_dir,
            text="Diretório de Arquivos:",
            font=(fonts["family"], fonts["size_medium"], "bold"),
            bg=cores["bg"],
            fg=cores["fg"]
        )
        label_dir.pack(anchor='w', pady=(0, 5))
        print("DEBUG: Label diretório criado")
        
        # Frame para entrada e botão
        frame_entrada = tk.Frame(frame_dir, bg=cores["bg"])
        frame_entrada.pack(fill=tk.X)
        
        entrada_dir = tk.Entry(
            frame_entrada,
            font=(fonts["family"], fonts["size_normal"]),
            bg=cores["text_bg"],
            fg=cores["fg"],
            relief=tk.SOLID,
            borderwidth=1
        )
        entrada_dir.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=5)
        print("DEBUG: Campo de entrada criado")
        
        # Carrega o diretório atual
        diretorio_atual = config_manager.obter_diretorio_config()
        if diretorio_atual:
            entrada_dir.delete(0, tk.END)
            entrada_dir.insert(0, diretorio_atual)
            print(f"DEBUG: Diretório carregado: {diretorio_atual}")
        else:
            print("DEBUG: Nenhum diretório configurado")
        
        def salvar_diretorio():
            """Salva o diretório digitado manualmente"""
            try:
                diretorio = entrada_dir.get().strip()
                if not diretorio:
                    messagebox.showwarning("Atenção", "Digite um diretório válido.")
                    return
                
                # Valida se o diretório existe
                if not os.path.exists(diretorio):
                    resposta = messagebox.askyesno(
                        "Diretório não existe",
                        f"O diretório não existe:\n{diretorio}\n\nDeseja criar?"
                    )
                    if not resposta:
                        return
                
                # Salva a configuração
                caminho_completo = config_manager.definir_diretorio_config(diretorio)
                if caminho_completo:
                    entrada_dir.delete(0, tk.END)
                    entrada_dir.insert(0, caminho_completo)
                    messagebox.showinfo("Sucesso", f"Diretório configurado:\n{caminho_completo}")
            except Exception as e:
                print(f"ERRO ao salvar diretório: {e}")
                messagebox.showerror("Erro", f"Erro ao salvar diretório:\n{e}")
        
        def procurar_diretorio():
            """Abre diálogo para escolher o diretório"""
            try:
                novo_dir = config_manager.solicitar_diretorio_usuario()
                if novo_dir:
                    entrada_dir.delete(0, tk.END)
                    entrada_dir.insert(0, novo_dir)
            except Exception as e:
                print(f"ERRO ao procurar diretório: {e}")
                messagebox.showerror("Erro", f"Erro ao procurar diretório:\n{e}")
        
        def resetar_diretorio():
            """Reseta o diretório para o padrão"""
            try:
                resposta = messagebox.askyesno(
                    "Confirmar Reset",
                    "Tem certeza que deseja resetar o diretório?\n\n"
                    "Isso fará com que o sistema pergunte novamente onde salvar os arquivos."
                )
                
                if resposta:
                    if config_manager.resetar_config():
                        entrada_dir.delete(0, tk.END)
                        messagebox.showinfo("Sucesso", "Configuração resetada com sucesso!")
            except Exception as e:
                print(f"ERRO ao resetar diretório: {e}")
                messagebox.showerror("Erro", f"Erro ao resetar diretório:\n{e}")
        
        # Botões
        frame_botoes_dir = tk.Frame(frame_entrada, bg=cores["bg"])
        frame_botoes_dir.pack(side=tk.LEFT, padx=(10, 0))
        
        btn_procurar = ttk.Button(
            frame_botoes_dir,
            text="Procurar",
            command=procurar_diretorio
        )
        btn_procurar.pack(side=tk.LEFT, padx=2)
        
        btn_salvar = ttk.Button(
            frame_botoes_dir,
            text="Salvar",
            command=salvar_diretorio
        )
        btn_salvar.pack(side=tk.LEFT, padx=2)
        
        btn_resetar = ttk.Button(
            frame_botoes_dir,
            text="Resetar",
            command=resetar_diretorio
        )
        btn_resetar.pack(side=tk.LEFT, padx=2)
        print("DEBUG: Botões criados")
        
        # Informação adicional
        info_text = (
            "Os arquivos de configuração (dominios_DDA.json, estrutura_layouts.json e filas_mq.json)\n"
            "serão salvos no diretório configurado dentro da pasta 'xmlforge_config'."
        )
        label_info = tk.Label(
            frame_principal,
            text=info_text,
            font=(fonts["family"], fonts["size_small"]),
            bg=cores["bg"],
            fg=cores["fg_secondary"],
            justify=tk.LEFT
        )
        label_info.pack(pady=(20, 10))
        
        # Botão Fechar
        btn_fechar = ttk.Button(
            frame_principal,
            text="Fechar",
            command=janela_config.destroy
        )
        btn_fechar.pack(pady=(10, 0))
        
        print("DEBUG: Tela de configurações completa!")
        
    except Exception as e:
        print(f"ERRO ao criar widgets: {e}")
        import traceback
        traceback.print_exc()
        messagebox.showerror("Erro", f"Erro ao criar tela de configurações:\n{e}")

def main():
    """Função principal para iniciar a aplicação"""
    global janela, campo_resultado, tag_var, combo, frame, menu_bar, menu_importacoes, formato_var
    
    janela = tk.Tk()
    janela.title("Gerador de XML DDA")

    largura_janela = 1100
    altura_janela = 800
    largura_tela = janela.winfo_screenwidth()
    altura_tela = janela.winfo_screenheight()
    x = (largura_tela // 2) - (largura_janela // 2)
    y = (altura_tela // 2) - (altura_janela // 2)
    janela.geometry(f"{largura_janela}x{altura_janela}+{x}+{y}")
    janela.minsize(1100, 700)  # Tamanho mínimo para garantir que todos os elementos fiquem visíveis
    
    # Configura a janela para expandir o conteúdo
    janela.rowconfigure(1, weight=1)  # Linha do campo de resultado se expande
    janela.columnconfigure(0, weight=1)  # Coluna se expande

    # Obtém configurações de cores e fontes
    cores = gerenciador_temas.get_cores()
    fonts = gerenciador_temas.get_font_config()
    spacing = gerenciador_temas.get_spacing_config()
    
    # Configura cor de fundo da janela
    janela.configure(bg=cores["bg"])

    # Menu principal
    menu_bar = tk.Menu(janela)
    menu_importacoes = tk.Menu(menu_bar, tearoff=0)
    menu_importacoes.add_command(label="Transformar XSD em JSON", command=importar_e_atualizar)
    menu_importacoes.add_command(label="Transformar Tags em JSON", command=abrir_tela_tags_para_json)
    menu_importacoes.add_command(label="Inclusão/Edição de Domínios", command=abrir_tela_inclusao_dominios)
    menu_bar.add_cascade(label="IMPORTAÇÕES", menu=menu_importacoes)
    
    # Menu Conexões
    menu_conexoes = tk.Menu(menu_bar, tearoff=0)
    menu_conexoes.add_command(label="Filas MQ", command=abrir_tela_filas_mq)
    menu_bar.add_cascade(label="CONEXÕES", menu=menu_conexoes)
    
    # Menu Configurações
    menu_configuracoes = tk.Menu(menu_bar, tearoff=0)
    menu_configuracoes.add_command(label="Diretório de Arquivos", command=abrir_tela_configuracoes)
    menu_bar.add_cascade(label="CONFIGURAÇÕES", menu=menu_configuracoes)
    
    janela.config(menu=menu_bar)

    # Frame principal com padding maior e fundo limpo
    frame = tk.Frame(janela, bg=cores["bg_secondary"], relief=tk.FLAT, borderwidth=0)
    frame.grid(row=0, column=0, sticky='ew', padx=spacing["lg"], pady=spacing["lg"])
    frame.columnconfigure(1, weight=1)

    # Label com estilo moderno
    label_combo = tk.Label(frame, text="Escolha uma mensagem:", 
                          bg=cores["bg_secondary"],
                          fg=cores["fg"],
                          font=(fonts["family"], fonts["size_medium"], "bold"))
    label_combo.grid(row=0, column=0, sticky='w', padx=(spacing["md"], spacing["sm"]))
    
    tag_var = tk.StringVar()
    
    # Combobox estilizado
    combo = ttk.Combobox(frame, textvariable=tag_var, values=[], width=45,
                        font=(fonts["family"], fonts["size_normal"]))
    combo.grid(row=0, column=1, padx=spacing["sm"], pady=spacing["md"], sticky='ew')

    # Botão principal com estilo
    botao_gerar = ttk.Button(frame, text="Gerar XML", command=gerar_saida)
    botao_gerar.grid(row=0, column=2, padx=(spacing["sm"], spacing["md"]), pady=spacing["md"])
    
    # Frame para formato do XML com melhor espaçamento
    frame_formato = tk.Frame(frame, bg=cores["bg_secondary"])
    frame_formato.grid(row=1, column=1, sticky='w', pady=(0, spacing["md"]))
    
    formato_var = tk.StringVar(value="formatado")
    
    # Label para formato
    label_formato = tk.Label(frame_formato, text="Formato:", 
                            bg=cores["bg_secondary"],
                            fg=cores["fg_secondary"],
                            font=(fonts["family"], fonts["size_small"]))
    label_formato.pack(side=tk.LEFT, padx=(0, spacing["sm"]))
    
    radio_formatado = ttk.Radiobutton(frame_formato, text="Formatado", 
                                       variable=formato_var, value="formatado",
                                       command=atualizar_formato)
    radio_formatado.pack(side=tk.LEFT, padx=(0, spacing["md"]))
    
    radio_minify = ttk.Radiobutton(frame_formato, text="Minificado", 
                                    variable=formato_var, value="minify",
                                    command=atualizar_formato)
    radio_minify.pack(side=tk.LEFT)
    
    # Separador vertical
    separador_mq = ttk.Separator(frame_formato, orient='vertical')
    separador_mq.pack(side=tk.LEFT, fill='y', padx=spacing["md"])
    
    # Label para Ambiente MQ
    label_ambiente_mq = tk.Label(frame_formato, text="Ambiente:",
                                bg=cores["bg_secondary"],
                                fg=cores["fg_secondary"],
                                font=(fonts["family"], fonts["size_small"]))
    label_ambiente_mq.pack(side=tk.LEFT, padx=(0, spacing["sm"]))
    
    # Dropdown de ambientes MQ
    ambiente_mq_var = tk.StringVar()
    combo_ambiente_mq = ttk.Combobox(frame_formato, textvariable=ambiente_mq_var,
                                     width=20, state="readonly",
                                     font=(fonts["family"], fonts["size_small"]))
    combo_ambiente_mq.pack(side=tk.LEFT, padx=(0, spacing["sm"]))
    
    # Label de status da conexão
    label_status_mq = tk.Label(frame_formato, text="● Offline",
                              bg=cores["bg_secondary"],
                              fg="#DC3545",  # Vermelho
                              font=(fonts["family"], fonts["size_small"], "bold"),
                              width=15,  # Largura fixa para não mover o layout
                              anchor="w")  # Alinha texto à esquerda
    label_status_mq.pack(side=tk.LEFT, padx=(0, spacing["md"]))
    
    # Botão Enviar na Fila
    botao_enviar_fila = ttk.Button(frame_formato, text="Enviar na Fila",
                                   command=lambda: enviar_xml_para_fila())
    botao_enviar_fila.pack(side=tk.LEFT, padx=(0, spacing["sm"]))
    
    def carregar_ambientes_mq():
        """Carrega a lista de ambientes do arquivo filas_mq.json"""
        json_path = config_manager.obter_diretorio_config()
        if json_path:
            json_path = os.path.join(json_path, "filas_mq.json")
        
        try:
            if json_path and os.path.exists(json_path):
                with open(json_path, "r", encoding="utf-8") as f:
                    filas = json.load(f)
                    ambientes = [fila.get("ambiente", "") for fila in filas if fila.get("ambiente")]
                    combo_ambiente_mq['values'] = ambientes
                    if ambientes:
                        combo_ambiente_mq.set(ambientes[0])
                        conectar_fila_mq(ambientes[0])
            else:
                combo_ambiente_mq['values'] = []
        except Exception as e:
            print(f"Erro ao carregar ambientes MQ: {str(e)}")
            combo_ambiente_mq['values'] = []
    
    def obter_config_ambiente(nome_ambiente):
        """Obtém a configuração completa de um ambiente"""
        json_path = config_manager.obter_diretorio_config()
        if json_path:
            json_path = os.path.join(json_path, "filas_mq.json")
        
        try:
            if json_path and os.path.exists(json_path):
                with open(json_path, "r", encoding="utf-8") as f:
                    filas = json.load(f)
                    for fila in filas:
                        if fila.get("ambiente") == nome_ambiente:
                            return fila
        except Exception as e:
            print(f"Erro ao obter configuração do ambiente: {str(e)}")
        return None
    
    def conectar_fila_mq(nome_ambiente, mostrar_erros=True):
        """Conecta com a fila MQ do ambiente selecionado"""
        global qmgr_connection, queue_connection, ambiente_atual
        
        if not PYMQI_DISPONIVEL:
            janela.after(0, lambda: label_status_mq.config(text="● Offline", fg="#DC3545"))
            if mostrar_erros:
                janela.after(0, lambda: messagebox.showwarning("pymqi não disponível",
                                     "O módulo pymqi não está instalado.\n\n"
                                     "Para instalar, execute:\npip install pymqi"))
            return False
        
        # Desconecta conexão anterior se existir (sem atualizar status)
        desconectar_fila_mq(atualizar_status=False)
        
        config = obter_config_ambiente(nome_ambiente)
        if not config:
            janela.after(0, lambda: label_status_mq.config(text="● Offline", fg="#DC3545"))
            if mostrar_erros:
                janela.after(0, lambda: messagebox.showerror("Erro", f"Configuração do ambiente '{nome_ambiente}' não encontrada."))
            return False
        
        try:
            # Tenta conectar com o Queue Manager
            conn_info = f"{config['host']}({config['porta']})"
            cd = pymqi.CD()
            cd.ChannelName = config['canal'].encode('utf-8')
            cd.ConnectionName = conn_info.encode('utf-8')
            cd.ChannelType = pymqi.CMQC.MQCHT_CLNTCONN
            cd.TransportType = pymqi.CMQC.MQXPT_TCP
            
            qmgr = pymqi.QueueManager(None)
            qmgr.connect_with_options(config['gerenciador'], cd=cd)
            
            qmgr_connection = qmgr
            ambiente_atual = nome_ambiente
            
            janela.after(0, lambda: label_status_mq.config(text="● Online", fg="#28A745"))  # Verde
            print(f"Conectado ao ambiente: {nome_ambiente}")
            return True
            
        except pymqi.MQMIError as e:
            janela.after(0, lambda: label_status_mq.config(text="● Offline", fg="#DC3545"))
            erro_msg = f"Erro ao conectar com MQ:\nCódigo: {e.comp}\nMotivo: {e.reason}"
            print(erro_msg)
            if mostrar_erros:
                janela.after(0, lambda msg=erro_msg: messagebox.showerror("Erro de Conexão MQ", msg))
            return False
        except Exception as e:
            janela.after(0, lambda: label_status_mq.config(text="● Offline", fg="#DC3545"))
            erro_msg = f"Erro inesperado ao conectar: {str(e)}"
            print(erro_msg)
            if mostrar_erros:
                janela.after(0, lambda msg=erro_msg: messagebox.showerror("Erro", msg))
            return False
    
    def desconectar_fila_mq(atualizar_status=True):
        """Desconecta da fila MQ"""
        global qmgr_connection, queue_connection, ambiente_atual
        
        try:
            if queue_connection:
                queue_connection.close()
                queue_connection = None
            
            if qmgr_connection:
                qmgr_connection.disconnect()
                qmgr_connection = None
            
            ambiente_atual = None
            
            # Só atualiza o status se explicitamente solicitado
            if atualizar_status:
                label_status_mq.config(text="● Offline", fg="#DC3545")
        except:
            pass
    
    def enviar_xml_para_fila():
        """Envia o XML minificado para a fila MQ"""
        global qmgr_connection, ambiente_atual
        
        if not PYMQI_DISPONIVEL:
            messagebox.showwarning("pymqi não disponível",
                                 "O módulo pymqi não está instalado.\n\n"
                                 "Para instalar, execute:\npip install pymqi")
            return
        
        # Verifica se há um ambiente selecionado
        ambiente_selecionado = ambiente_mq_var.get()
        if not ambiente_selecionado:
            messagebox.showwarning("Ambiente não selecionado",
                                 "Selecione um ambiente antes de enviar.")
            return
        
        # Obtém o XML do campo
        xml_content = campo_resultado.get("1.0", tk.END).strip()
        if not xml_content:
            messagebox.showwarning("XML vazio",
                                 "Não há conteúdo XML para enviar.")
            return
        
        # Minifica o XML
        xml_minificado = minificar_xml(xml_content)
        
        try:
            # Verifica/reconecta se necessário
            if not qmgr_connection or ambiente_atual != ambiente_selecionado:
                if not conectar_fila_mq(ambiente_selecionado):
                    return
            
            # Obtém configuração do ambiente
            config = obter_config_ambiente(ambiente_selecionado)
            if not config:
                messagebox.showerror("Erro", "Configuração do ambiente não encontrada.")
                return
            
            # Abre a fila para escrita
            queue = pymqi.Queue(qmgr_connection, config['fila'])
            
            # Envia a mensagem
            queue.put(xml_minificado.encode('utf-8'))
            
            # Fecha a fila
            queue.close()
            
            messagebox.showinfo("Sucesso",
                              f"XML enviado com sucesso para a fila!\n\n"
                              f"Ambiente: {ambiente_selecionado}\n"
                              f"Fila: {config['fila']}\n"
                              f"Tamanho: {len(xml_minificado)} bytes")
            
        except pymqi.MQMIError as e:
            erro_msg = f"Erro ao enviar mensagem para MQ:\n\nCódigo: {e.comp}\nMotivo: {e.reason}"
            print(erro_msg)
            messagebox.showerror("Erro de Envio MQ", erro_msg)
            label_status_mq.config(text="● Offline", fg="#DC3545")
            qmgr_connection = None
        except Exception as e:
            erro_msg = f"Erro inesperado ao enviar mensagem:\n\n{str(e)}"
            print(erro_msg)
            messagebox.showerror("Erro", erro_msg)
    
    # Evento de mudança no combo de ambientes
    def ao_selecionar_ambiente(event):
        ambiente = ambiente_mq_var.get()
        if ambiente:
            # Atualiza status para "Conectando..." imediatamente
            label_status_mq.config(text="● Conectando...", fg="#B8860B")  # Amarelo escuro
            
            # Inicia conexão em thread separada para não travar a interface
            def conectar_em_background():
                conectar_fila_mq(ambiente, mostrar_erros=True)
            
            thread = threading.Thread(target=conectar_em_background, daemon=True)
            thread.start()
    
    combo_ambiente_mq.bind('<<ComboboxSelected>>', ao_selecionar_ambiente)
    
    # Carrega os ambientes ao iniciar
    carregar_ambientes_mq()

    # Container para o campo de resultado com borda sutil
    container_resultado = tk.Frame(janela, bg=cores["border"], relief=tk.FLAT)
    container_resultado.grid(row=1, column=0, padx=spacing["lg"], pady=(0, spacing["lg"]), sticky='nsew')
    
    # Frame para campo de resultado com números de linha
    frame_resultado = tk.Frame(container_resultado, bg=cores["text_bg"], 
                              relief=tk.FLAT, borderwidth=1,
                              highlightthickness=1,
                              highlightbackground=cores["border"],
                              highlightcolor=cores["entry_focus"])
    frame_resultado.pack(fill=tk.BOTH, expand=True, padx=1, pady=1)
    
    # Text widget para números de linha com estilo moderno
    numeros_linha = tk.Text(frame_resultado, width=5, padx=spacing["sm"], takefocus=0,
                            border=0,
                            background=cores["line_numbers_bg"],
                            foreground=cores["line_numbers_fg"],
                            state='disabled',
                            wrap='none',
                            font=(fonts["family_mono"], fonts["size_normal"]),
                            relief=tk.FLAT,
                            highlightthickness=0)
    numeros_linha.pack(side=tk.LEFT, fill=tk.Y)
    
    # Separador vertical entre números de linha e conteúdo
    separador = tk.Frame(frame_resultado, width=1, bg=cores["line_numbers_border"])
    separador.pack(side=tk.LEFT, fill=tk.Y)
    
    # Frame para conter o Text widget e as scrollbars
    frame_text_container = tk.Frame(frame_resultado, bg=cores["text_bg"])
    frame_text_container.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    
    # Scrollbar vertical com estilo moderno (igual à tela de domínios)
    scrollbar_resultado = ttk.Scrollbar(frame_text_container, orient=tk.VERTICAL)
    scrollbar_resultado.pack(side=tk.RIGHT, fill=tk.Y)
    
    # Scrollbar horizontal
    scrollbar_horizontal = ttk.Scrollbar(frame_text_container, orient=tk.HORIZONTAL)
    scrollbar_horizontal.pack(side=tk.BOTTOM, fill=tk.X)
    
    # Text widget para o conteúdo XML com estilo moderno
    campo_resultado = tk.Text(frame_text_container, width=120, height=40, 
                              wrap=tk.NONE,
                              font=(fonts["family_mono"], fonts["size_normal"]),
                              relief=tk.FLAT,
                              borderwidth=0,
                              highlightthickness=0,
                              padx=spacing["sm"],
                              pady=spacing["sm"],
                              fg="#000000",
                              bg=cores["text_bg"],
                              insertbackground="#000000",
                              autoseparators=True,
                              undo=True,
                              yscrollcommand=scrollbar_resultado.set,
                              xscrollcommand=scrollbar_horizontal.set)
    campo_resultado.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    
    # Configura as tags de formatação
    campo_resultado.tag_config("tag_xml", foreground="#0066CC")
    
    # Desabilita a propagação automática de tags ao digitar
    def ao_inserir_texto(event):
        """Aplica formatação correta ao texto sendo digitado"""
        if event.char and event.char.isprintable():
            # Agenda a aplicação da formatação após a inserção do caractere
            campo_resultado.after(1, aplicar_formatacao_dinamica)
        return None
    
    def ao_modificar_texto(event=None):
        """Monitora modificações no texto para aplicar formatação"""
        campo_resultado.after(10, aplicar_formatacao_dinamica)
    
    def aplicar_formatacao_dinamica():
        """Aplica formatação dinamicamente nas linhas modificadas"""
        try:
            # Obtém a posição do cursor
            pos_cursor = campo_resultado.index(tk.INSERT)
            linha_atual = int(pos_cursor.split('.')[0])
            
            # Aplica formatação apenas na linha atual e adjacentes para performance
            inicio_linha = max(1, linha_atual - 1)
            fim_linha = linha_atual + 1
            
            # Remove formatação antiga da região
            campo_resultado.tag_remove("tag_xml", f"{inicio_linha}.0", f"{fim_linha}.end")
            
            # Pega o texto das linhas
            texto = campo_resultado.get(f"{inicio_linha}.0", f"{fim_linha}.end")
            
            # Aplica cor azul em todas as tags (incluindo < e >)
            # Tag de abertura: <TagName>
            for match in re.finditer(r'<\w+[^>]*>', texto):
                start_pos = match.start()
                end_pos = match.end()
                
                # Converte posição relativa para absoluta
                linha = texto[:start_pos].count('\n') + inicio_linha
                coluna = start_pos - texto[:start_pos].rfind('\n') - 1 if '\n' in texto[:start_pos] else start_pos
                inicio = f"{linha}.{coluna}"
                
                linha_fim = texto[:end_pos].count('\n') + inicio_linha
                coluna_fim = end_pos - texto[:end_pos].rfind('\n') - 1 if '\n' in texto[:end_pos] else end_pos
                fim = f"{linha_fim}.{coluna_fim}"
                
                campo_resultado.tag_add("tag_xml", inicio, fim)
            
            # Tag de fechamento: </TagName>
            for match in re.finditer(r'</\w+>', texto):
                start_pos = match.start()
                end_pos = match.end()
                
                linha = texto[:start_pos].count('\n') + inicio_linha
                coluna = start_pos - texto[:start_pos].rfind('\n') - 1 if '\n' in texto[:start_pos] else start_pos
                inicio = f"{linha}.{coluna}"
                
                linha_fim = texto[:end_pos].count('\n') + inicio_linha
                coluna_fim = end_pos - texto[:end_pos].rfind('\n') - 1 if '\n' in texto[:end_pos] else end_pos
                fim = f"{linha_fim}.{coluna_fim}"
                
                campo_resultado.tag_add("tag_xml", inicio, fim)
            
            # Tag auto-fechada: <TagName/>
            for match in re.finditer(r'<\w+/>', texto):
                start_pos = match.start()
                end_pos = match.end()
                
                linha = texto[:start_pos].count('\n') + inicio_linha
                coluna = start_pos - texto[:start_pos].rfind('\n') - 1 if '\n' in texto[:start_pos] else start_pos
                inicio = f"{linha}.{coluna}"
                
                linha_fim = texto[:end_pos].count('\n') + inicio_linha
                coluna_fim = end_pos - texto[:end_pos].rfind('\n') - 1 if '\n' in texto[:end_pos] else end_pos
                fim = f"{linha_fim}.{coluna_fim}"
                
                campo_resultado.tag_add("tag_xml", inicio, fim)
        except Exception as e:
            pass  # Ignora erros durante edição
    
    def ao_colar_texto(event=None):
        """Remove tags do texto colado para que fique na cor preta"""
        # Agenda a remoção das tags para após o paste ser completado
        campo_resultado.after(10, remover_tags_texto_colado)
        return None
    
    def remover_tags_texto_colado():
        """Remove a tag_xml de todo o conteúdo para garantir que valores fiquem pretos"""
        try:
            # Aplica novamente apenas as tags nas estruturas XML, não nos valores
            aplicar_formatacao_tags_especificas()
        except:
            pass
    
    def ao_duplo_clique(event):
        """Comportamento customizado para duplo clique: seleciona valor ou nome da tag"""
        try:
            # Cancela a seleção padrão do duplo clique
            campo_resultado.after_idle(lambda: selecionar_texto_xml())
            return "break"  # Impede comportamento padrão
        except:
            pass
    
    def selecionar_texto_xml():
        """Seleciona valor da tag ou nome da tag baseado na posição do clique"""
        try:
            # Obtém a posição do cursor
            pos_cursor = campo_resultado.index(tk.INSERT)
            linha, coluna = map(int, pos_cursor.split('.'))
            
            # Obtém a linha completa
            linha_texto = campo_resultado.get(f"{linha}.0", f"{linha}.end")
            
            if coluna >= len(linha_texto):
                return
            
            # Procura os caracteres mais próximos antes da posição do cursor
            ultimo_abre = linha_texto.rfind('<', 0, coluna + 1)  # Último < antes ou na posição
            ultimo_fecha = linha_texto.rfind('>', 0, coluna)      # Último > antes da posição
            
            # Procura o próximo < depois da posição
            proximo_abre = linha_texto.find('<', coluna)
            
            # Determina se está em um valor ou dentro de uma tag
            # Se o > mais recente está mais próximo que o < mais recente, está em um VALOR
            if ultimo_fecha != -1 and ultimo_fecha > ultimo_abre and proximo_abre != -1:
                # Está em um VALOR entre tags: procura por > antes e < depois
                valor = linha_texto[ultimo_fecha + 1:proximo_abre]
                
                if valor and valor.strip():  # Se há conteúdo não-vazio
                    # Seleciona o valor
                    campo_resultado.tag_remove(tk.SEL, "1.0", tk.END)
                    campo_resultado.tag_add(tk.SEL, 
                                          f"{linha}.{ultimo_fecha + 1}", 
                                          f"{linha}.{proximo_abre}")
                    campo_resultado.mark_set(tk.INSERT, f"{linha}.{proximo_abre}")
            
            # Se o < mais recente está mais próximo, está dentro de uma TAG
            elif ultimo_abre != -1 and ultimo_abre > ultimo_fecha:
                # Procura o > que fecha esta tag
                proximo_fecha = linha_texto.find('>', coluna)
                
                if proximo_fecha != -1:
                    # Extrai o conteúdo da tag sem < e >
                    conteudo_tag = linha_texto[ultimo_abre + 1:proximo_fecha]
                    
                    # Remove / se for tag de fechamento
                    if conteudo_tag.startswith('/'):
                        nome_tag = conteudo_tag[1:].strip()
                        inicio_nome = ultimo_abre + 2  # Pula < e /
                    else:
                        # Remove atributos se houver (pega só o nome)
                        nome_tag = conteudo_tag.split()[0].strip()
                        inicio_nome = ultimo_abre + 1  # Pula só <
                    
                    # Seleciona apenas o nome da tag
                    campo_resultado.tag_remove(tk.SEL, "1.0", tk.END)
                    campo_resultado.tag_add(tk.SEL, 
                                          f"{linha}.{inicio_nome}", 
                                          f"{linha}.{inicio_nome + len(nome_tag)}")
                    campo_resultado.mark_set(tk.INSERT, f"{linha}.{inicio_nome + len(nome_tag)}")
        except Exception as e:
            print(f"Erro ao selecionar texto: {e}")
    
    campo_resultado.bind('<Key>', ao_inserir_texto)
    campo_resultado.bind('<BackSpace>', ao_modificar_texto)
    campo_resultado.bind('<Delete>', ao_modificar_texto)
    campo_resultado.bind('<<Paste>>', ao_colar_texto)
    campo_resultado.bind('<Control-v>', ao_colar_texto)
    campo_resultado.bind('<Control-V>', ao_colar_texto)
    campo_resultado.bind('<Control-x>', ao_modificar_texto)
    campo_resultado.bind('<Control-X>', ao_modificar_texto)
    campo_resultado.bind('<Double-Button-1>', ao_duplo_clique)
    
    # Configura as scrollbars para controlar o Text widget
    scrollbar_resultado.config(command=campo_resultado.yview)
    scrollbar_horizontal.config(command=campo_resultado.xview)
    
    def atualizar_numeros_linha(event=None):
        """Atualiza os números de linha"""
        numeros_linha.config(state='normal')
        numeros_linha.delete(1.0, tk.END)
        
        # Pega o número total de linhas
        linha_final = int(campo_resultado.index('end-1c').split('.')[0])
        
        # Adiciona os números de linha com espaçamento adequado
        linha_numeros = '\n'.join(str(i).rjust(3) for i in range(1, linha_final + 1))
        numeros_linha.insert(1.0, linha_numeros)
        numeros_linha.config(state='disabled')
        
        # Atualiza o destaque das linhas selecionadas
        atualizar_destaque_linhas_selecionadas()
    
    def atualizar_destaque_linhas_selecionadas(event=None):
        """Destaca os números das linhas que estão selecionadas no campo de resultado"""
        numeros_linha.config(state='normal')
        
        # Remove destaque anterior
        numeros_linha.tag_remove("selected_line", "1.0", tk.END)
        
        # Configura a tag de destaque com cor azul claro
        numeros_linha.tag_config("selected_line", background="#C5D9F1", foreground="#000000")
        
        # Verifica se há seleção no campo_resultado
        try:
            # Pega as posições inicial e final da seleção
            sel_start = campo_resultado.index(tk.SEL_FIRST)
            sel_end = campo_resultado.index(tk.SEL_LAST)
            
            # Extrai os números das linhas
            linha_inicio = int(sel_start.split('.')[0])
            linha_fim = int(sel_end.split('.')[0])
            
            # Destaca as linhas selecionadas nos números
            for linha in range(linha_inicio, linha_fim + 1):
                # Posição no widget de números (linha - 1 porque é 0-indexed no conteúdo)
                start_idx = f"{linha}.0"
                end_idx = f"{linha}.end"
                numeros_linha.tag_add("selected_line", start_idx, end_idx)
        except tk.TclError:
            # Não há seleção ou cursor simples
            # Destaca apenas a linha atual do cursor
            try:
                cursor_pos = campo_resultado.index(tk.INSERT)
                linha_cursor = int(cursor_pos.split('.')[0])
                start_idx = f"{linha_cursor}.0"
                end_idx = f"{linha_cursor}.end"
                numeros_linha.tag_add("selected_line", start_idx, end_idx)
            except:
                pass
        
        numeros_linha.config(state='disabled')
    
    # Define a função global para ser chamada por outras funções
    global atualizar_numeros_linha_func
    atualizar_numeros_linha_func = atualizar_numeros_linha
    
    def sincronizar_scroll(*args):
        """Sincroniza a rolagem entre o campo de resultado e os números de linha"""
        scrollbar_resultado.set(*args)
        numeros_linha.yview_moveto(float(args[0]))
    
    # Configura a sincronização de scroll
    campo_resultado.config(yscrollcommand=sincronizar_scroll)
    
    # Atualiza números quando o conteúdo mudar
    campo_resultado.bind('<<Modified>>', lambda e: (atualizar_numeros_linha(), campo_resultado.edit_modified(False)))
    campo_resultado.bind('<KeyRelease>', lambda e: (atualizar_numeros_linha(), atualizar_destaque_linhas_selecionadas()))
    
    # Atualiza destaque de linhas quando a seleção mudar
    campo_resultado.bind('<<Selection>>', atualizar_destaque_linhas_selecionadas)
    campo_resultado.bind('<ButtonRelease-1>', atualizar_destaque_linhas_selecionadas)
    
    # Binding para Ctrl+F - Buscar e Substituir
    campo_resultado.bind('<Control-f>', lambda e: abrir_buscar_substituir())
    campo_resultado.bind('<Control-F>', lambda e: abrir_buscar_substituir())
    
    # Inicializa os números de linha
    atualizar_numeros_linha()

    parser.carregar_json()
    combo["values"] = parser.TAGS_XML
    if parser.TAGS_XML:
        tag_var.set(parser.TAGS_XML[0])

    # Aplica tema inicial
    aplicar_tema()
    
    # Protocolo de fechamento da janela
    def ao_fechar_aplicacao():
        """Desconecta da fila MQ antes de fechar a aplicação"""
        desconectar_fila_mq()
        janela.destroy()
    
    janela.protocol("WM_DELETE_WINDOW", ao_fechar_aplicacao)

    janela.mainloop()

if __name__ == "__main__":
    main()
