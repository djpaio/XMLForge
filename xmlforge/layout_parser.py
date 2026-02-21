import os
import json
import xml.etree.ElementTree as ET
from tkinter import messagebox, filedialog
from xmlforge.utils import valor_padrao, montar_xml
from xmlforge import config_manager

TAGS_XML = []
ESTRUTURA = {}
TIPOS = {}
DOMINIOS = {}
TEMPLATES = {}
ns = {'xs': 'http://www.w3.org/2001/XMLSchema'}

def carregar_json():
    global ESTRUTURA, TAGS_XML, DOMINIOS, TEMPLATES
    
    # Obtém o diretório configurado (sem perguntar ao usuário, apenas verifica se existe)
    diretorio = config_manager.obter_diretorio_config()
    
    # Carrega estrutura_layouts.json
    if diretorio:
        estrutura_path = os.path.join(diretorio, "estrutura_layouts.json")
    else:
        estrutura_path = "estrutura_layouts.json"  # Fallback para o diretório atual
    
    if os.path.exists(estrutura_path):
        with open(estrutura_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            # Separa os templates das estruturas de mensagens
            TEMPLATES = data.pop("_templates", {})
            ESTRUTURA = data
        TAGS_XML.clear()
        TAGS_XML.extend(sorted(ESTRUTURA.keys()))
    
    # Carrega domínios
    if diretorio:
        dominios_path = os.path.join(diretorio, "dominios_DDA.json")
    else:
        dominios_path = "dominios_DDA.json"  # Fallback para o diretório atual
    
    if os.path.exists(dominios_path):
        with open(dominios_path, "r", encoding="utf-8") as f:
            DOMINIOS = json.load(f)

def selecionar_arquivos_xsd():
    arquivos = filedialog.askopenfilenames(filetypes=[("Arquivos XSD", "*.xsd")])
    if arquivos:
        gerar_estrutura_xsds(arquivos)
        carregar_json()

def extrair_tipos_simples(root):
    for simple in root.findall(".//xs:simpleType", ns):
        nome = simple.attrib.get("name")
        if not nome:
            continue
        TIPOS[nome] = ""

def resolver_tags(tipo, complexos):
    def processar(tipo_local, visitados):
        if tipo_local in visitados:
            return {}  # Evita recursão infinita

        visitados.add(tipo_local)
        estrutura = {}
        if tipo_local in complexos:
            complexo = complexos[tipo_local]
            for seq in complexo.findall(".//xs:sequence", ns):
                for el in seq.findall("xs:element", ns):
                    tag_nome = el.attrib.get("name")
                    tag_tipo = el.attrib.get("type", "xs:string")
                    if tag_nome:
                        tag_tipo = tag_tipo.replace(":", "")
                        if tag_tipo in complexos:
                            estrutura[tag_nome] = processar(tag_tipo, visitados.copy())
                        else:
                            estrutura[tag_nome] = valor_padrao(tag_tipo)
        visitados.remove(tipo_local)
        return estrutura
    return processar(tipo, set())

def gerar_estrutura_xsds(lista_arquivos):
    estrutura_nova = {}
    try:
        for caminho in lista_arquivos:
            if caminho.lower().endswith(".xsd"):
                try:
                    tree = ET.parse(caminho)
                    root = tree.getroot()
                    extrair_tipos_simples(root)
                    complexos = {
                        ct.attrib['name']: ct
                        for ct in root.findall(".//xs:complexType", ns)
                        if 'name' in ct.attrib
                    }
                    for elem in root.findall(".//xs:element", ns):
                        nome = elem.attrib.get("name")
                        tipo = elem.attrib.get("type")
                        if nome and tipo and (nome.startswith("DDA") or nome.startswith("ADDA")):
                            tipo = tipo.replace(":", "")
                            estrutura_nova[nome] = resolver_tags(tipo, complexos)
                except Exception as e:
                    print(f"Erro ao processar {os.path.basename(caminho)}: {e}")
        
        # Obtém o caminho do arquivo (pergunta ao usuário se necessário)
        json_path = config_manager.obter_caminho_arquivo("estrutura_layouts.json")
        if not json_path:
            messagebox.showinfo("Cancelado", "Operação de salvamento cancelada.")
            return
        
        templates = {}
        if os.path.exists(json_path):
            with open(json_path, "r", encoding="utf-8") as f:
                estrutura_antiga = json.load(f)
                # Preserva os templates se existirem
                templates = estrutura_antiga.pop("_templates", {})
        else:
            estrutura_antiga = {}
        
        estrutura_antiga.update(estrutura_nova)
        
        # Adiciona os templates de volta antes de salvar
        if templates:
            estrutura_antiga["_templates"] = templates
        
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(estrutura_antiga, f, indent=2, ensure_ascii=False)
        
        messagebox.showinfo("Sucesso", f"Estruturas XSD salvas em:\n{json_path}")
    except Exception as e:
        messagebox.showerror("Erro ao gerar estrutura dos XSDs", str(e))

def extrair_tags(tag):
    nome_tag = tag.strip("<>")
    if nome_tag not in ESTRUTURA:
        return f"Estrutura para {tag} não encontrada."
    estrutura = ESTRUTURA[nome_tag]
    xml_gerado = [f"<{nome_tag}>"]
    for filho, filhos_netos in estrutura.items():
        xml_gerado.append(montar_xml(filho, filhos_netos, nivel=1, dominios=DOMINIOS, nome_mensagem=nome_tag))
    xml_gerado.append(f"</{nome_tag}>")
    return "\n".join(xml_gerado)
