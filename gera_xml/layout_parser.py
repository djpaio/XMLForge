import os
import json
import xml.etree.ElementTree as ET
from tkinter import messagebox, filedialog
from utils import valor_padrao, montar_xml

TAGS_XML = []
ESTRUTURA = {}
TIPOS = {}
ns = {'xs': 'http://www.w3.org/2001/XMLSchema'}

def carregar_json():
    global ESTRUTURA, TAGS_XML
    if os.path.exists("estrutura_layouts.json"):
        with open("estrutura_layouts.json", "r", encoding="utf-8") as f:
            ESTRUTURA = json.load(f)
        TAGS_XML.clear()
        TAGS_XML.extend(sorted(ESTRUTURA.keys()))

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
    def processar(tipo_local):
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
                            estrutura[tag_nome] = processar(tag_tipo)
                        else:
                            estrutura[tag_nome] = valor_padrao(tag_tipo)
        return estrutura
    return processar(tipo)

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
        if os.path.exists("estrutura_layouts.json"):
            with open("estrutura_layouts.json", "r", encoding="utf-8") as f:
                estrutura_antiga = json.load(f)
        else:
            estrutura_antiga = {}
        estrutura_antiga.update(estrutura_nova)
        with open("estrutura_layouts.json", "w", encoding="utf-8") as f:
            json.dump(estrutura_antiga, f, indent=2, ensure_ascii=False)
    except Exception as e:
        messagebox.showerror("Erro ao gerar estrutura dos XSDs", str(e))

def extrair_tags(tag):
    nome_tag = tag.strip("<>")
    if nome_tag not in ESTRUTURA:
        return f"Estrutura para {tag} não encontrada."
    estrutura = ESTRUTURA[nome_tag]
    xml_gerado = [f"<{nome_tag}>"]
    for filho, filhos_netos in estrutura.items():
        xml_gerado.append(montar_xml(filho, filhos_netos, nivel=1))
    xml_gerado.append(f"</{nome_tag}>")
    return "\n".join(xml_gerado)
