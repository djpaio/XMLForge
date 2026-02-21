import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
import re
import json
import os
import layout_parser as parser

def gerar_saida():
    campo_resultado.delete(1.0, tk.END)
    tag = tag_var.get()
    if tag:
        xml = parser.extrair_tags(tag)
        campo_resultado.insert(tk.END, xml)

def importar_e_atualizar():
    parser.selecionar_arquivos_xsd()
    combo["values"] = parser.TAGS_XML
    if parser.TAGS_XML:
        tag_var.set(parser.TAGS_XML[0])

def agrupar_por_grupo(tags):
    estrutura = {}
    pilha = [estrutura]
    nomes_grupos = []
    for tag in tags:
        tag = tag.strip()
        if not tag:
            continue

        if tag.startswith("Grupo_"):
            novo_grupo = {}
            pilha[-1][tag] = novo_grupo
            pilha.append(novo_grupo)
            nomes_grupos.append(tag)
        elif tag.startswith("/Grupo_") or tag.startswith("</Grupo_"):
            if len(pilha) > 1:
                pilha.pop()
        elif tag.startswith("/") or tag.startswith("</"):
            continue  # ignorar fechamentos de outras tags
        else:
            pilha[-1][tag] = ""

    return estrutura

def abrir_tela_tags_para_json():
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

    def incluir_no_json():
        nome_msg = entrada_nome.get().strip()
        if not nome_msg:
            messagebox.showerror("Erro", "Digite o nome da mensagem (ex: DDA0001E)")
            return
        linhas = campo_resultado_tags.get("1.0", tk.END).splitlines()
        tags_limpas = [linha.strip() for linha in linhas if linha.strip()]
        estrutura = agrupar_por_grupo(tags_limpas)
        if not estrutura:
            messagebox.showwarning("Aviso", "Nenhuma tag encontrada para incluir.")
            return

        json_path = "estrutura_layouts.json"
        if os.path.exists(json_path):
            with open(json_path, "r", encoding="utf-8") as f:
                atual = json.load(f)
        else:
            atual = {}

        atual[nome_msg] = estrutura

        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(atual, f, indent=2, ensure_ascii=False)

        parser.carregar_json()
        combo["values"] = parser.TAGS_XML
        if parser.TAGS_XML:
            tag_var.set(parser.TAGS_XML[0])

        messagebox.showinfo("Sucesso", f"Mensagem '{nome_msg}' incluída com sucesso no JSON!")
        janela_tags.destroy()

    janela_tags = tk.Toplevel(janela)
    janela_tags.title("Transformar Tags em JSON")
    largura = 600
    altura = 600
    largura_tela = janela.winfo_screenwidth()
    altura_tela = janela.winfo_screenheight()
    x = (largura_tela // 2) - (largura // 2)
    y = (altura_tela // 2) - (altura // 2)
    janela_tags.geometry(f"{largura}x{altura}+{x}+{y}")

    tk.Label(janela_tags, text="Cole abaixo o conteúdo com as tags:").pack(anchor="w", padx=10, pady=(10, 2))
    campo_input = scrolledtext.ScrolledText(janela_tags, width=70, height=10)
    campo_input.pack(padx=10, pady=5)

    botao_limpar = ttk.Button(janela_tags, text="Extrair Tags", command=limpar_tags)
    botao_limpar.pack(pady=5)

    tk.Label(janela_tags, text="Tags encontradas:").pack(anchor="w", padx=10)
    campo_resultado_tags = scrolledtext.ScrolledText(janela_tags, width=70, height=15)
    campo_resultado_tags.pack(padx=10, pady=5)

    frame_inferior = ttk.Frame(janela_tags)
    frame_inferior.pack(pady=10)
    tk.Label(frame_inferior, text="Nome da mensagem:").grid(row=0, column=0, padx=5)
    entrada_nome = ttk.Entry(frame_inferior)
    entrada_nome.grid(row=0, column=1, padx=5)
    botao_incluir = ttk.Button(frame_inferior, text="Incluir no JSON", command=incluir_no_json)
    botao_incluir.grid(row=0, column=2, padx=10)

janela = tk.Tk()
janela.title("Gerador de XML DDA")

largura_janela = 1000
altura_janela = 750
largura_tela = janela.winfo_screenwidth()
altura_tela = janela.winfo_screenheight()
x = (largura_tela // 2) - (largura_janela // 2)
y = (altura_tela // 2) - (altura_janela // 2)
janela.geometry(f"{largura_janela}x{altura_janela}+{x}+{y}")

# Menu principal
menu_bar = tk.Menu(janela)
menu_importacoes = tk.Menu(menu_bar, tearoff=0)
menu_importacoes.add_command(label="Transformar XSD em JSON", command=importar_e_atualizar)
menu_importacoes.add_command(label="Transformar Tags em JSON", command=abrir_tela_tags_para_json)
menu_bar.add_cascade(label="IMPORTAÇÕES", menu=menu_importacoes)
janela.config(menu=menu_bar)

# Frame principal
frame = ttk.Frame(janela, padding=10)
frame.grid(row=0, column=0, sticky='w')

label_combo = ttk.Label(frame, text="Escolha uma mensagem:")
label_combo.grid(row=0, column=0, sticky='w')
tag_var = tk.StringVar()
combo = ttk.Combobox(frame, textvariable=tag_var, values=[], width=40)
combo.grid(row=0, column=1, padx=5, pady=5)

botao_gerar = ttk.Button(frame, text="Gerar XML", command=gerar_saida)
botao_gerar.grid(row=0, column=2, padx=5)

campo_resultado = scrolledtext.ScrolledText(janela, width=120, height=40)
campo_resultado.grid(row=1, column=0, padx=10, pady=10)

parser.carregar_json()
combo["values"] = parser.TAGS_XML
if parser.TAGS_XML:
    tag_var.set(parser.TAGS_XML[0])

janela.mainloop()
