def valor_padrao(tipo):
    return ""

def montar_xml(tag, filhos, nivel=1):
    indent = "\t" * nivel
    if isinstance(filhos, dict) and filhos:
        linhas = [f"{indent}<{tag}>"]
        for filho, neto in filhos.items():
            linhas.append(montar_xml(filho, neto, nivel + 1))
        linhas.append(f"{indent}</{tag}>")
        return "\n".join(linhas)
    else:
        return f"{indent}<{tag}></{tag}>"