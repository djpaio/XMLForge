"""
Teste da tela de Configurações
"""
import tkinter as tk
from tkinter import ttk
import sys
import os

# Adiciona o diretório ao path
sys.path.insert(0, os.path.dirname(__file__))

from xmlforge import config_manager
from xmlforge.temas import GerenciadorTemas

# Cria janela de teste
janela = tk.Tk()
janela.title("Teste - Tela de Configurações")
janela.geometry("400x300")

gerenciador_temas = GerenciadorTemas()

def abrir_tela_configuracoes():
    """Abre a tela de configurações do sistema - VERSÃO DE TESTE"""
    from tkinter import messagebox
    
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
    
    # Título
    titulo = tk.Label(
        frame_principal,
        text="Configurações",
        font=(fonts["family"], fonts["size_large"], "bold"),
        bg=cores["bg"],
        fg=cores["primary"]
    )
    titulo.pack(pady=(0, 20))
    
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
    
    # Carrega o diretório atual
    diretorio_atual = config_manager.obter_diretorio_config()
    if diretorio_atual:
        entrada_dir.delete(0, tk.END)
        entrada_dir.insert(0, diretorio_atual)
    
    def salvar_diretorio():
        """Salva o diretório digitado manualmente"""
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
    
    def procurar_diretorio():
        """Abre diálogo para escolher o diretório"""
        novo_dir = config_manager.solicitar_diretorio_usuario()
        if novo_dir:
            entrada_dir.delete(0, tk.END)
            entrada_dir.insert(0, novo_dir)
    
    def resetar_diretorio():
        """Reseta o diretório para o padrão"""
        resposta = messagebox.askyesno(
            "Confirmar Reset",
            "Tem certeza que deseja resetar o diretório?\n\n"
            "Isso fará com que o sistema pergunte novamente onde salvar os arquivos."
        )
        
        if resposta:
            if config_manager.resetar_config():
                entrada_dir.delete(0, tk.END)
                messagebox.showinfo("Sucesso", "Configuração resetada com sucesso!")
    
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
        fg=cores["text_secondary"],
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

# Botão para abrir a tela
btn_teste = ttk.Button(janela, text="Abrir Tela de Configurações", command=abrir_tela_configuracoes)
btn_teste.pack(expand=True)

janela.mainloop()
