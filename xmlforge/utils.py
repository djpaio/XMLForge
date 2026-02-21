import re
from datetime import datetime

def valor_padrao(tipo):
    return ""

def processar_template_com_dominios(template_xml, dominios=None):
    """
    Processa um template XML e adiciona marcadores para tags que possuem domínios ou informações.
    - Domínios: adiciona ⟪...⟫ (seleção de valores)
    - Informações: adiciona ícone ℹ️ antes da tag
    
    Args:
        template_xml: String com XML do template (header ou footer)
        dominios: Dicionário com os domínios/informações disponíveis
    
    Returns:
        String com XML processado
    """
    if not dominios:
        return template_xml
    
    # Regex para encontrar tags vazias: <Tag></Tag> ou <Tag/>
    # Captura o nome da tag
    def substituir_tag_vazia(match):
        nome_tag = match.group(1)
        # Se a tag tem domínio ou informação, adiciona o marcador apropriado
        if nome_tag in dominios:
            tipo = dominios[nome_tag].get("tipo", "dominio")
            if tipo == "informacao":
                # Para informação, deixa tag vazia (ícone será adicionado visualmente depois)
                return f"<{nome_tag}></{nome_tag}>"
            else:
                return f"<{nome_tag}>⟪...⟫</{nome_tag}>"
        else:
            # Mantém como estava
            return match.group(0)
    
    # Substitui tags auto-fechadas <Tag/>
    template_xml = re.sub(r'<(\w+)/>', substituir_tag_vazia, template_xml)
    
    # Substitui tags vazias <Tag></Tag>
    template_xml = re.sub(r'<(\w+)></\1>', substituir_tag_vazia, template_xml)
    
    return template_xml

def montar_xml(tag, filhos, nivel=1, dominios=None, nome_mensagem=None):
    indent = "\t" * nivel
    if isinstance(filhos, dict) and filhos:
        linhas = [f"{indent}<{tag}>"]
        for filho, neto in filhos.items():
            linhas.append(montar_xml(filho, neto, nivel + 1, dominios, nome_mensagem))
        linhas.append(f"{indent}</{tag}>")
        return "\n".join(linhas)
    else:
        # Caso especial: preenche CodMsg automaticamente com o nome da mensagem
        if tag == "CodMsg" and nome_mensagem:
            return f"{indent}<{tag}>{nome_mensagem}</{tag}>"
        # Caso especial: preenche tags de Data e Hora automaticamente (DtHr*)
        elif tag.startswith("DtHr"):
            data_hora_atual = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
            return f"{indent}<{tag}>{data_hora_atual}</{tag}>"
        # Caso especial: preenche tags de Data automaticamente (Dt* mas não DtHr*)
        elif tag.startswith("Dt"):
            data_atual = datetime.now().strftime("%Y-%m-%d")
            return f"{indent}<{tag}>{data_atual}</{tag}>"
        # Verifica se a tag tem domínio ou informação
        elif dominios and tag in dominios:
            tipo = dominios[tag].get("tipo", "dominio")
            # Marca com caracteres especiais para identificar depois
            if tipo == "informacao":
                # Para informação, deixa tag vazia (ícone será adicionado visualmente depois)
                return f"{indent}<{tag}></{tag}>"
            else:
                return f"{indent}<{tag}>⟪...⟫</{tag}>"
        else:
            return f"{indent}<{tag}></{tag}>"