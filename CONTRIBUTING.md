# 🤝 Guia de Contribuição

Obrigado por considerar contribuir com o XMLForge! Este documento fornece diretrizes para contribuir com o projeto.

## 📋 Índice

- [Código de Conduta](#código-de-conduta)
- [Como Posso Contribuir?](#como-posso-contribuir)
- [Configuração do Ambiente](#configuração-do-ambiente)
- [Processo de Desenvolvimento](#processo-de-desenvolvimento)
- [Padrões de Código](#padrões-de-código)
- [Commits e Pull Requests](#commits-e-pull-requests)
- [Reportando Bugs](#reportando-bugs)
- [Sugerindo Melhorias](#sugerindo-melhorias)

---

## 🤝 Código de Conduta

Este projeto segue o [Contributor Covenant Code of Conduct](https://www.contributor-covenant.org/). Ao participar, você concorda em manter um ambiente respeitoso e acolhedor.

---

## 🎯 Como Posso Contribuir?

### 🐛 Reportando Bugs

Antes de criar um relatório de bug:
- Verifique se já não existe uma issue sobre o problema
- Use a versão mais recente do código
- Colete informações sobre o bug

**Ao reportar um bug, inclua:**
- Descrição clara e concisa
- Passos para reproduzir
- Comportamento esperado vs. atual
- Screenshots (se aplicável)
- Ambiente (Python version, OS, etc.)

### ✨ Sugerindo Melhorias

Para sugerir melhorias:
1. Abra uma issue com a tag `enhancement`
2. Descreva a funcionalidade desejada
3. Explique por que seria útil
4. Forneça exemplos de uso

### 💻 Contribuindo com Código

1. Verifique as issues abertas
2. Comente na issue que deseja trabalhar
3. Aguarde aprovação do mantenedor
4. Fork o projeto e crie sua branch
5. Implemente as mudanças
6. Envie um Pull Request

---

## ⚙️ Configuração do Ambiente

### 1. Fork e Clone

```bash
# Fork no GitHub, depois:
git clone https://github.com/SEU_USUARIO/xmlforge.git
cd xmlforge
```

### 2. Ambiente Virtual

```bash
python -m venv .venv

# Windows
.venv\Scripts\activate

# Linux/Mac
source .venv/bin/activate
```

### 3. Instalar Dependências

```bash
pip install -r requirements.txt

# Instalar ferramentas de desenvolvimento
pip install pylint flake8 black isort
```

### 4. Configurar Pre-commit (opcional)

```bash
pip install pre-commit
pre-commit install
```

---

## 🔄 Processo de Desenvolvimento

### 1. Criar Branch

```bash
git checkout -b feature/nome-da-feature
# ou
git checkout -b fix/nome-do-bug
```

**Convenção de nomes:**
- `feature/` - Novas funcionalidades
- `fix/` - Correções de bugs
- `docs/` - Alterações na documentação
- `refactor/` - Refatorações de código
- `test/` - Adição de testes

### 2. Desenvolver

- Mantenha mudanças focadas e atômicas
- Escreva código limpo e legível
- Adicione comentários quando necessário
- Siga os padrões de código (veja abaixo)

### 3. Testar

```bash
# Execute a aplicação
python -m gera_xml.app

# Teste as funcionalidades alteradas
# TODO: Adicionar testes automatizados
```

### 4. Formatar Código

```bash
# Formata código automaticamente
black gera_xml/

# Organiza imports
isort gera_xml/

# Verifica PEP 8
flake8 gera_xml/

# Análise estática
pylint gera_xml/
```

---

## 📏 Padrões de Código

### Python Style Guide

Seguimos [PEP 8](https://pep8.org/) com algumas adaptações:

#### Naming Conventions

```python
# Classes: PascalCase
class GerenciadorTemas:
    pass

# Funções e variáveis: snake_case
def gerar_saida():
    nome_tag = "exemplo"

# Constantes: UPPER_SNAKE_CASE
MAX_RETRIES = 3
DEFAULT_TIMEOUT = 30
```

#### Imports

```python
# 1. Biblioteca padrão
import json
import os
from datetime import datetime

# 2. Bibliotecas de terceiros
import pymqi

# 3. Módulos locais
from gera_xml import layout_parser
from gera_xml.temas import GerenciadorTemas
```

#### Docstrings

Use docstrings para todas as funções públicas:

```python
def minificar_xml(xml: str) -> str:
    """
    Remove espaços e quebras de linha do XML.
    
    Args:
        xml: String contendo XML formatado
        
    Returns:
        String com XML minificado
        
    Example:
        >>> xml = "<tag>\\n  <inner/>\\n</tag>"
        >>> minificar_xml(xml)
        '<tag><inner/></tag>'
    """
    return re.sub(r'>\s+<', '><', xml.strip())
```

#### Type Hints

Use type hints sempre que possível (Python 3.8+):

```python
def processar_template(
    template: str, 
    dominios: Optional[Dict[str, Any]] = None
) -> str:
    """Processa template com domínios."""
    if dominios is None:
        dominios = {}
    return template
```

#### Formatação

```python
# Máximo de 100 caracteres por linha (não 79)
# Strings longas: use parênteses
mensagem = (
    "Esta é uma mensagem muito longa que "
    "precisa ser quebrada em múltiplas linhas"
)

# Listas/dicts longos: um item por linha
configuracao = {
    "host": "localhost",
    "porta": 1414,
    "canal": "DEV.CHANNEL",
}
```

---

## 📝 Commits e Pull Requests

### Mensagens de Commit

Use [Conventional Commits](https://www.conventionalcommits.org/):

```
tipo(escopo): descrição curta

Descrição mais detalhada (opcional)

Relacionado: #123
```

**Tipos:**
- `feat`: Nova funcionalidade
- `fix`: Correção de bug
- `docs`: Documentação
- `style`: Formatação (sem mudança de código)
- `refactor`: Refatoração de código
- `test`: Adição de testes
- `chore`: Manutenção

**Exemplos:**

```bash
git commit -m "feat(mq): adiciona retry automático em falhas de conexão"
git commit -m "fix(xml): corrige formatação de tags vazias"
git commit -m "docs(readme): atualiza instruções de instalação"
```

### Pull Requests

**Antes de enviar:**
- [ ] Código formatado (black, isort)
- [ ] Sem erros de lint (flake8)
- [ ] Funcionalidades testadas manualmente
- [ ] Documentação atualizada (se aplicável)
- [ ] CHANGELOG.md atualizado (se aplicável)

**Template de PR:**

```markdown
## Descrição
Breve descrição das mudanças

## Tipo de mudança
- [ ] Bug fix
- [ ] Nova funcionalidade
- [ ] Breaking change
- [ ] Documentação

## Como testar
1. Execute...
2. Clique em...
3. Verifique que...

## Checklist
- [ ] Código segue o style guide
- [ ] Mudanças foram testadas
- [ ] Documentação atualizada
- [ ] Sem warnings de lint

## Screenshots (se aplicável)
```

---

## 🐛 Reportando Bugs

### Template de Issue

```markdown
**Descrição do Bug**
Descrição clara e concisa do bug

**Como Reproduzir**
1. Vá para '...'
2. Clique em '...'
3. Role até '...'
4. Veja o erro

**Comportamento Esperado**
O que deveria acontecer

**Comportamento Atual**
O que realmente acontece

**Screenshots**
Se aplicável, adicione screenshots

**Ambiente:**
 - OS: [Windows 10]
 - Python: [3.10.0]
 - Versão: [1.0.0]

**Contexto Adicional**
Qualquer outra informação relevante
```

---

## ✨ Sugerindo Melhorias

### Template de Feature Request

```markdown
**A sua feature está relacionada a um problema?**
Descrição clara do problema: "Eu sempre fico frustrado quando..."

**Descreva a solução que você gostaria**
Descrição clara do que você quer que aconteça

**Descreva alternativas consideradas**
Outras soluções ou features que você considerou

**Contexto Adicional**
Screenshots, mockups, exemplos de outras ferramentas
```

---

## 📚 Recursos Adicionais

- [Python Style Guide (PEP 8)](https://pep8.org/)
- [Conventional Commits](https://www.conventionalcommits.org/)
- [How to Write a Git Commit Message](https://chris.beams.io/posts/git-commit/)
- [GitHub Flow](https://guides.github.com/introduction/flow/)

---

## ❓ Dúvidas?

Se tiver dúvidas sobre contribuição:
- Abra uma issue com a tag `question`
- Entre em contato: deividjpaio@gmail.com

---

**Obrigado por contribuir! 🎉**
