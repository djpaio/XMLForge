# 📝 Changelog

Todas as mudanças notáveis neste projeto serão documentadas neste arquivo.

O formato é baseado em [Keep a Changelog](https://keepachangelog.com/pt-BR/1.0.0/),
e este projeto adere ao [Semantic Versioning](https://semver.org/lang/pt-BR/).

## [2.0.0] - 2026-02-21

### 🚀 Nova Versão Robusta com Melhorias Significativas

### ✨ Adicionado
- Sistema de gerenciamento de configurações aprimorado
- Melhorias na interface do usuário e experiência
- Refatoração do código para melhor manutenibilidade
- Testes automatizados (test_config.py, test_tela_config.py)
- Documentação expandida (DESIGN_SYSTEM.md, MIGRATION.md)
- Suporte aprimorado para diferentes ambientes

### 🔧 Melhorado
- Arquitetura do projeto reestruturada
- Performance otimizada na geração de XML
- Sistema de temas mais robusto
- Tratamento de erros aprimorado
- Gerenciamento de configurações centralizado

### 📚 Documentação
- Guia de contribuição (CONTRIBUTING.md)
- Sistema de design documentado
- Guia de migração entre versões

## [1.0.0] - 2026-02-20

### 🎉 Lançamento Inicial do XMLForge

### ✨ Adicionado
- Interface gráfica moderna com Tkinter
- Importação e conversão de arquivos XSD para JSON
- Geração automática de XML baseada em estruturas XSD
- Sistema de templates (R1 e R2) com headers e footers customizados
- Formatação inteligente (formatado vs minificado)
- Auto-preenchimento de campos de data/hora e código de mensagem
- Sistema de domínios de valores pré-definidos
- Tooltips informativos para campos com domínios
- Integração com IBM MQ (conexão, envio de mensagens)
- Gerenciamento de múltiplos ambientes MQ
- Conexão assíncrona para não travar a interface
- Indicadores visuais de status de conexão (Online/Offline/Conectando)
- Sistema de buscar e substituir com suporte a regex
- Seleção inteligente: duplo clique em tags ou valores
- Syntax highlighting para XML (tags em azul, valores em preto)
- Formatação dinâmica em tempo real durante edição
- Destaque especial para tags Acto (verde) e Recsd (vermelho)
- Números de linha com scrollbar sincronizada
- Barra de rolagem horizontal para XMLs extensos
- Suporte completo a copiar/colar mantendo formatação
- Sistema de temas com paleta de cores profissional
- Ferramenta de transformação de tags em JSON
- Validação de estrutura XML conforme XSD

### 🔧 Funcionalidades Técnicas
- Threading para operações MQ em background
- Persistência de configurações em JSON
- Gerenciamento robusto de erros e exceções
- Arquitetura modular (app, parser, temas, utils)
- Suporte a Python 3.8+
- Compatibilidade com Windows

### 📚 Documentação
- README.md completo e profissional
- AVALIACAO_TECNICA.md com análise detalhada
- DESIGN_SYSTEM.md com sistema de design
- CONTRIBUTING.md com guia de contribuição
- LICENSE MIT incluída
- Docstrings em funções principais

### 🛠️ Infraestrutura
- Arquivo .gitignore configurado
- Arquivo .gitattributes para encoding
- Setup.py para instalação via pip
- Requirements.txt com dependências
- Estrutura de pacote Python adequada

---

## [Unreleased]

### 🚧 Em Desenvolvimento
- Testes unitários automatizados
- Suporte a mais formatos de templates
- Export para diferentes formatos
- Histórico de mensagens enviadas
- Validação avançada de XML contra XSD
- Modo escuro/claro alternável
- Atalhos de teclado customizáveis
- Plugin system para extensões

### 💡 Planejado
- Suporte a Linux e macOS
- Interface web (opcional)
- Integração com outras filas (RabbitMQ, Kafka)
- Geração de documentação automática
- Sistema de logs avançado
- Perfis de usuário
- Importação de XMLs existentes

---

## Tipos de Mudanças

- `✨ Adicionado` - Novas funcionalidades
- `🔄 Modificado` - Mudanças em funcionalidades existentes
- `⚠️ Depreciado` - Funcionalidades que serão removidas
- `🗑️ Removido` - Funcionalidades removidas
- `🐛 Corrigido` - Correções de bugs
- `🔒 Segurança` - Correções de vulnerabilidades
- `📚 Documentação` - Mudanças apenas em documentação
- `🛠️ Infraestrutura` - Mudanças em build, CI/CD, etc.

---

[1.0.0]: https://github.com/deividjpaio/xmlforge/releases/tag/v1.0.0
