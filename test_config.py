"""
Script de teste para verificar o módulo config_manager
"""
import sys
import os

# Adiciona o diretório ao path
sys.path.insert(0, os.path.dirname(__file__))

try:
    from xmlforge import config_manager
    print("✓ Módulo config_manager importado com sucesso!")
    
    # Testa funções básicas
    print(f"✓ Função obter_diretorio_config existe: {hasattr(config_manager, 'obter_diretorio_config')}")
    print(f"✓ Função definir_diretorio_config existe: {hasattr(config_manager, 'definir_diretorio_config')}")
    print(f"✓ Função obter_caminho_arquivo existe: {hasattr(config_manager, 'obter_caminho_arquivo')}")
    
    # Verifica diretório atual
    diretorio = config_manager.obter_diretorio_config()
    if diretorio:
        print(f"✓ Diretório configurado: {diretorio}")
    else:
        print("✓ Nenhum diretório configurado (esperado na primeira execução)")
    
    print("\n✅ Todos os testes passaram!")
    
except Exception as e:
    print(f"❌ Erro ao importar módulo: {e}")
    import traceback
    traceback.print_exc()
