# 🚀 XMLForge

[![Python Version](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Platform](https://img.shields.io/badge/platform-Windows-lightgrey.svg)](https://www.microsoft.com/windows)

> Professional XML Generator from XSD schemas with modern GUI and IBM MQ integration.

## 📋 Índice

- [Sobre o Projeto](#sobre-o-projeto)
- [Funcionalidades](#funcionalidades)
- [Pré-requisitos](#pré-requisitos)
- [Instalação](#instalação)
- [Como Usar](#como-usar)
- [Estrutura do Projeto](#estrutura-do-projeto)
- [Tecnologias Utilizadas](#tecnologias-utilizadas)
- [Configuração](#configuração)
- [Contribuindo](#contribuindo)
- [Licença](#licença)
- [Autor](#autor)

---

## 📖 Sobre o Projeto

**XMLForge** is a professional desktop application developed in Python that facilitates the creation, editing, and management of XML messages following predefined XSD schemas. The tool was designed for corporate environments that need to generate standardized XMLs quickly and reliably, with support for value domains, custom templates, and integration with IBM MQ messaging systems.

### 🎯 Objetivo

Simplify the process of creating complex XML messages, eliminating formatting errors and ensuring compliance with XSD schemas through an intuitive and modern interface.

---

## ✨ Funcionalidades

### 📝 Geração de XML
- ✅ **Importação de esquemas XSD** - Conversão automática de arquivos XSD para estruturas JSON
- ✅ **Geração automática de XML** - Criação de XMLs baseados em templates pré-definidos
- ✅ **Formatação inteligente** - Suporte para XML formatado (indentado) ou minificado
- ✅ **Auto-preenchimento** - Campos de data/hora e códigos de mensagem preenchidos automaticamente
- ✅ **Templates R1 e R2** - Suporte para diferentes tipos de mensagens com headers/footers customizados

### 🎨 Interface Moderna
- 🖥️ **Design profissional** - Interface clean inspirada em sistemas web modernos
- 🌈 **Sistema de temas** - Paleta de cores consistente e elegante
- 📊 **Números de linha** - Visualização clara com numeração lateral
- 🔍 **Buscar e substituir** - Ferramenta de busca avançada com regex e substituição usando Ctrl+F
- 📏 **Seleção inteligente** - Duplo clique seleciona tags ou valores corretamente
- 🎯 **Syntax highlighting** - Tags XML em azul, valores em preto

### 🔧 Ferramentas Avançadas
- 📚 **Gerenciamento de domínios** - Sistema de valores pré-definidos para tags específicas
- ℹ️ **Tooltips informativos** - Informações contextuais sobre campos e valores
- 🔄 **Conversão de Tags** - Transformação de texto em estrutura JSON
- ⚡ **Formatação dinâmica** - Cores aplicadas em tempo real durante edição
- 📋 **Copiar/colar** - Suporte completo com preservação de formatação

### 🔗 Integração MQ
- 📡 **Conexão IBM MQ** - Integração nativa com filas IBM MQ via pymqi
- 🌐 **Múltiplos ambientes** - Gerenciamento de diferentes ambientes (DEV, HML, PRD)
- 🔄 **Conexão assíncrona** - Conexões em background sem travar a interface
- 📤 **Envio direto** - Envio de XML minificado diretamente para filas MQ
- 🟢 **Status em tempo real** - Indicadores visuais de conexão (Online/Offline/Conectando)

### 🛠️ Recursos Adicionais
- 💾 **Persistência de configurações** - Filas MQ e domínios armazenados em JSON
- 🔒 **Validação de estrutura** - Garantia de conformidade com esquemas XSD
- 📊 **Barras de rolagem** - Suporte para XMLs horizontalmente extensos
- ⌨️ **Atalhos de teclado** - Ctrl+C, Ctrl+V, Ctrl+X funcionais
- 🎨 **Destaque de campos** - Tags Acto (verde) e Recsd (vermelho)

---

## 🔧 Pré-requisitos

Antes de começar, certifique-se de ter instalado:

- **Python 3.8+** - [Download aqui](https://www.python.org/downloads/)
- **pip** - Gerenciador de pacotes Python (incluído com Python 3.8+)
- **IBM MQ Client** (opcional) - Necessário apenas para funcionalidades MQ
  - [Download IBM MQ Client](https://www.ibm.com/support/pages/downloading-ibm-mq-clients)

### 📦 Dependências Python

```txt
pymqi>=1.12.0  # IBM MQ integration (opcional)
```

> **Nota:** O Tkinter já vem incluído com Python no Windows. Não é necessário instalação adicional.

---

## 📥 Instalação

### 1️⃣ Clone o repositório

```bash
git clone https://github.com/seu-usuario/xmlforge.git
cd xmlforge
```

### 2️⃣ (Opcional) Crie um ambiente virtual

```bash
# Windows
python -m venv .venv
.venv\Scripts\activate

# Linux/Mac
python3 -m venv .venv
source .venv/bin/activate
```

### 3️⃣ Instale as dependências

```bash
pip install -r requirements.txt
```

> **Nota:** Se não for usar funcionalidades MQ, você pode pular a instalação do `pymqi`. O sistema detectará automaticamente e desabilitará apenas as funcionalidades MQ.

### 4️⃣ (Opcional) Instale via setup.py

```bash
pip install -e .
```

Isso permite executar o programa de qualquer lugar:

```bash
xmlforge
```

---

## 🚀 Como Usar

### Execução Normal

```bash
python -m xmlforge.app
```

Ou diretamente:

```bash
python xmlforge/app.py
```

### Fluxo de Trabalho Típico

#### 1. **Importar Estrutura XSD** (primeira vez)
   - Menu: `IMPORTAÇÕES > Transformar XSD em JSON`
   - Selecione os arquivos `.xsd` desejados
   - O sistema gerará o arquivo `estrutura_layouts.json`

#### 2. **Selecionar Mensagem**
   - No dropdown principal, escolha a mensagem desejada (ex: `DDA0101R1`)
   - Clique em **"Gerar XML"**

#### 3. **Editar XML** (se necessário)
   - Preencha valores vazios
   - Use duplo clique para selecionar tags ou valores
   - Edite diretamente no campo (coloração automática)

#### 4. **Formatar XML**
   - **Formatado**: XML indentado e legível
   - **Minificado**: XML compacto, sem espaços

#### 5. **Enviar para Fila MQ** (opcional)
   - Selecione o ambiente no dropdown
   - Aguarde status "● Online"
   - Clique em **"Enviar na Fila"**

---

## 📁 Estrutura do Projeto

```
xmlforge/
│
├── xmlforge/                    # Source code
│   ├── __init__.py
│   ├── app.py                   # Main application (UI)
│   ├── layout_parser.py         # XSD parser and XML generation
│   ├── temas.py                 # Theme and color system
│   └── utils.py                 # Utility functions
│
├── dominios_DDA.json            # Predefined value domains
├── estrutura_layouts.json       # Structure extracted from XSDs
├── filas_mq.json                # MQ environment configurations
│
├── .gitignore                   # Files ignored by Git
├── requirements.txt             # Python dependencies
├── setup.py                     # Installation configuration
├── versao.txt                   # Project version
│
├── AVALIACAO_TECNICA.md         # Technical project report
├── DESIGN_SYSTEM.md             # Design system documentation
└── README.md                    # This file
```
│
├── dominios_DDA.json            # Domínios de valores pré-definidos
├── estrutura_layouts.json       # Estrutura extraída dos XSDs
├── filas_mq.json                # Configurações de ambientes MQ
│
├── .gitignore                   # Arquivos ignorados pelo Git
├── requirements.txt             # Dependências Python
├── setup.py                     # Configuração de instalação
├── versao.txt                   # Versão do projeto
│
├── AVALIACAO_TECNICA.md         # Relatório técnico do projeto
├── DESIGN_SYSTEM.md             # Documentação do design system
└── README.md                    # Este arquivo
```

---

## 🛠️ Tecnologias Utilizadas

| Tecnologia | Versão | Propósito |
|------------|--------|-----------|
| **Python** | 3.8+ | Linguagem principal |
| **Tkinter** | Built-in | Interface gráfica nativa |
| **pymqi** | 1.12+ | Integração IBM MQ |
| **JSON** | Built-in | Armazenamento de configurações |
| **XML/XSD** | - | Formato de mensagens |
| **Threading** | Built-in | Operações assíncronas |
| **Regex (re)** | Built-in | Processamento de texto |

---

## ⚙️ Configuração

### Arquivos de Configuração

#### 📄 `dominios_DDA.json`
Define valores pré-definidos para campos específicos:

```json
{
  "TpAmbnt": {
    "tipo": "dominio",
    "valores": ["P", "H", "T"],
    "descricoes": {
      "P": "Produção",
      "H": "Homologação",
      "T": "Teste"
    }
  }
}
```

#### 📄 `filas_mq.json`
Configurações de ambientes IBM MQ:

```json
[
  {
    "ambiente": "DESENVOLVIMENTO",
    "host": "mq-dev.empresa.com",
    "porta": "1414",
    "gerenciador": "QM_DEV",
    "canal": "CANAL.DEV",
    "fila": "FILA.XML.DEV"
  }
]
```

#### 📄 `estrutura_layouts.json`
Gerado automaticamente pela importação de XSDs. Contém a estrutura completa das mensagens.

---

## 🤝 Contribuindo

Contribuições são sempre bem-vindas! Para contribuir:

1. **Fork** o projeto
2. Crie uma **branch** para sua feature (`git checkout -b feature/MinhaFeature`)
3. **Commit** suas mudanças (`git commit -m 'Adiciona MinhaFeature'`)
4. **Push** para a branch (`git push origin feature/MinhaFeature`)
5. Abra um **Pull Request**

### 📏 Padrões de Código

- Siga a [PEP 8](https://pep8.org/)
- Adicione docstrings em todas as funções
- Escreva testes para novas funcionalidades
- Mantenha funções pequenas e focadas

### 🐛 Reportando Bugs

Encontrou um bug? Abra uma [issue](../../issues) com:
- Descrição clara do problema
- Passos para reproduzir
- Comportamento esperado vs. atual
- Screenshots (se aplicável)
- Versão do Python e SO

---

## 📄 Licença

Este projeto está sob a licença MIT. Veja o arquivo [LICENSE](LICENSE) para mais detalhes.

---

## 👤 Autor

**Deivid Jhonatan Paio**

- Email: deividjpaio@gmail.com
- LinkedIn: [linkedin.com/in/deividjpaio](https://linkedin.com/in/deividjpaio)
- GitHub: [@deividjpaio](https://github.com/deividjpaio)

---

## 📝 Notas de Versão

### v1.0.0 (2026-02-20)
- ✨ Release inicial
- 🎨 Interface gráfica moderna com Tkinter
- 📝 Geração de XML a partir de XSD
- 🔗 Integração com IBM MQ
- 📚 Sistema de domínios e templates
- 🔍 Buscar e substituir com regex
- 🎯 Seleção inteligente de tags/valores
- ⚡ Formatação dinâmica em tempo real

---

## 🙏 Agradecimentos

- Comunidade Python pela excelente documentação
- IBM pela biblioteca pymqi
- Todos os contribuidores do projeto

---

<div align="center">

**⭐ Se este projeto foi útil, considere dar uma estrela!**

[⬆ Voltar ao topo](#-xmlforge)

</div>
