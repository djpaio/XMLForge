"""
Gerenciador de Configurações do XMLForge
Gerencia o diretório onde os arquivos de configuração são salvos
"""
import os
import json
from tkinter import filedialog, messagebox

# Nome do arquivo de configuração local (salvo no diretório do aplicativo)
CONFIG_FILE = "xmlforge_config.json"

# Nome da pasta que será criada no diretório escolhido pelo usuário
CONFIG_FOLDER_NAME = "xmlforge_config"

def carregar_config():
    """
    Carrega a configuração do arquivo local.
    Retorna um dict com as configurações ou um dict vazio se não existir.
    """
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"Erro ao carregar configuração: {e}")
            return {}
    return {}

def salvar_config(config):
    """
    Salva a configuração no arquivo local.
    """
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        print(f"Erro ao salvar configuração: {e}")
        return False

def obter_diretorio_config():
    """
    Retorna o diretório configurado para salvar os arquivos.
    Se não estiver configurado, retorna None.
    """
    config = carregar_config()
    return config.get("diretorio_arquivos", None)

def definir_diretorio_config(diretorio):
    """
    Define o diretório de configuração.
    Cria a pasta xmlforge_config se não existir.
    """
    if not diretorio:
        return False
    
    # Cria o caminho completo com a pasta xmlforge_config
    caminho_completo = os.path.join(diretorio, CONFIG_FOLDER_NAME)
    
    # Cria a pasta se não existir
    try:
        os.makedirs(caminho_completo, exist_ok=True)
    except Exception as e:
        messagebox.showerror("Erro", f"Não foi possível criar o diretório:\n{str(e)}")
        return False
    
    # Salva a configuração
    config = carregar_config()
    config["diretorio_arquivos"] = caminho_completo
    
    if salvar_config(config):
        return caminho_completo
    return False

def solicitar_diretorio_usuario():
    """
    Abre um diálogo para o usuário escolher o diretório.
    Cria a pasta xmlforge_config e salva a configuração.
    Retorna o caminho completo ou None se cancelado.
    """
    diretorio = filedialog.askdirectory(
        title="Escolha onde salvar os arquivos de configuração",
        mustexist=True
    )
    
    if diretorio:
        caminho_completo = definir_diretorio_config(diretorio)
        if caminho_completo:
            messagebox.showinfo(
                "Diretório Configurado",
                f"Arquivos de configuração serão salvos em:\n{caminho_completo}"
            )
            return caminho_completo
    
    return None

def obter_caminho_arquivo(nome_arquivo):
    """
    Retorna o caminho completo para um arquivo de configuração.
    Se o diretório não estiver configurado, solicita ao usuário.
    
    Args:
        nome_arquivo: Nome do arquivo (ex: "dominios_DDA.json")
    
    Returns:
        Caminho completo do arquivo ou None se cancelado
    """
    diretorio = obter_diretorio_config()
    
    # Se não está configurado, pergunta ao usuário
    if not diretorio:
        resposta = messagebox.askyesno(
            "Configurar Diretório",
            "É necessário configurar o diretório onde os arquivos serão salvos.\n\n"
            "Deseja escolher o diretório agora?"
        )
        
        if resposta:
            diretorio = solicitar_diretorio_usuario()
            if not diretorio:
                return None
        else:
            return None
    
    return os.path.join(diretorio, nome_arquivo)

def resetar_config():
    """
    Remove a configuração, voltando ao estado inicial.
    """
    if os.path.exists(CONFIG_FILE):
        try:
            os.remove(CONFIG_FILE)
            return True
        except Exception as e:
            messagebox.showerror("Erro", f"Não foi possível resetar a configuração:\n{str(e)}")
            return False
    return True

def obter_caminho_arquivo_sem_prompt(nome_arquivo):
    """
    Retorna o caminho completo para um arquivo de configuração.
    NÃO pergunta ao usuário se não estiver configurado.
    Retorna o caminho no diretório atual como fallback.
    
    Args:
        nome_arquivo: Nome do arquivo (ex: "dominios_DDA.json")
    
    Returns:
        Caminho completo do arquivo (ou nome simples se não configurado)
    """
    diretorio = obter_diretorio_config()
    
    if diretorio:
        return os.path.join(diretorio, nome_arquivo)
    else:
        # Fallback: diretório atual
        return nome_arquivo
