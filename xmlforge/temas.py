"""
Módulo de gerenciamento de cores para o Gerador de XML DDA
Design System - Paleta Profissional e Moderna
"""

class GerenciadorTemas:
    """Classe para gerenciar cores da aplicação com design moderno"""
    
    def __init__(self):
        # ===== PALETA DE CORES MODERNA E PROFISSIONAL =====
        # Inspirada em sistemas web modernos com tons suaves e elegantes
        
        self.CORES = {
            # --- Cores de Fundo ---
            "bg": "#F8F9FA",              # Cinza muito claro (fundo principal)
            "bg_secondary": "#FFFFFF",     # Branco puro (cards e painéis)
            "bg_tertiary": "#E9ECEF",      # Cinza claro (áreas secundárias)
            "bg_hover": "#F1F3F5",         # Hover sutil
            
            # --- Cores de Texto ---
            "fg": "#212529",               # Cinza escuro (texto principal)
            "fg_secondary": "#6C757D",     # Cinza médio (texto secundário)
            "fg_muted": "#ADB5BD",         # Cinza claro (texto desativado)
            
            # --- Cores de Campos de Texto ---
            "text_bg": "#FFFFFF",          # Branco para campos de texto
            "text_fg": "#212529",          # Texto escuro para contraste
            "text_border": "#DEE2E6",      # Borda suave
            "text_focus": "#4C9AFF",       # Azul para foco
            
            # --- Cores de Seleção ---
            "select_bg": "#4C9AFF",        # Azul moderno
            "select_fg": "#FFFFFF",        # Branco para contraste
            
            # --- Cores de Botões ---
            "button_bg": "#4C9AFF",        # Azul principal
            "button_fg": "#FFFFFF",        # Texto branco
            "button_hover": "#2980EF",     # Azul mais escuro no hover
            "button_secondary": "#E9ECEF", # Botões secundários
            "button_secondary_fg": "#495057", # Texto botões secundários
            
            # --- Cores de Entrada ---
            "entry_bg": "#FFFFFF",
            "entry_border": "#CED4DA",
            "entry_focus": "#4C9AFF",
            
            # --- Cores de Labels ---
            "label_fg": "#495057",
            "label_accent": "#4C9AFF",
            
            # --- Cores de Menu ---
            "menu_bg": "#FFFFFF",
            "menu_fg": "#212529",
            "menu_hover_bg": "#F8F9FA",
            "menu_accent": "#4C9AFF",
            
            # --- Cores de Alertas e Status ---
            "success": "#28A745",          # Verde para sucesso
            "warning": "#FFC107",          # Amarelo para avisos
            "error": "#DC3545",            # Vermelho para erros
            "info": "#17A2B8",             # Azul claro para informações
            
            # --- Cores Específicas de Formatação XML ---
            "tag_verde": "#D4EDDA",        # Verde suave (tags Acto)
            "tag_verde_border": "#28A745", # Borda verde
            "tag_vermelho": "#F8D7DA",     # Rosa suave (tags Recsd)
            "tag_vermelho_border": "#DC3545", # Borda vermelha
            "tag_amarelo": "#FFF3CD",      # Amarelo suave (domínios)
            "tag_amarelo_border": "#FFC107", # Borda amarela
            "tag_link": "#4C9AFF",         # Azul para links
            "tag_link_hover": "#2980EF",   # Azul escuro no hover
            
            # --- Cores de Bordas e Divisores ---
            "border": "#DEE2E6",
            "border_light": "#E9ECEF",
            "divider": "#CED4DA",
            
            # --- Cores de Scrollbar ---
            "scrollbar_bg": "#F8F9FA",
            "scrollbar_thumb": "#CED4DA",
            "scrollbar_thumb_hover": "#ADB5BD",
            
            # --- Cores de Grid/Tabela ---
            "grid_header_bg": "#E9ECEF",
            "grid_header_fg": "#495057",
            "grid_border": "#DEE2E6",
            "grid_row_hover": "#F8F9FA",
            "grid_row_selected": "#E7F3FF",
            
            # --- Cores de Números de Linha ---
            "line_numbers_bg": "#F1F3F5",
            "line_numbers_fg": "#6C757D",
            "line_numbers_border": "#DEE2E6",
            
            # --- Sombras (valores para usar em configurações) ---
            "shadow_color": "#00000015",   # Sombra suave
            "shadow_strong": "#00000030",  # Sombra mais forte
        }
    
    def get_cores(self):
        """Retorna as cores do tema"""
        return self.CORES
    
    def get_font_config(self):
        """Retorna configurações de fontes padronizadas"""
        return {
            "family": "Segoe UI",          # Fonte moderna e clean
            "family_mono": "Consolas",     # Fonte monoespaçada para código
            "size_small": 9,
            "size_normal": 10,
            "size_medium": 11,
            "size_large": 12,
            "size_xlarge": 14,
            "size_title": 16,
        }
    
    def get_spacing_config(self):
        """Retorna configurações de espaçamento padronizadas"""
        return {
            "xs": 4,
            "sm": 8,
            "md": 12,
            "lg": 16,
            "xl": 20,
            "xxl": 24,
        }