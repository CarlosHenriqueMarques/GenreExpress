# processador_lexique.py (Versão Excel FINAL com limpeza de dados)
# Fonte dos dados:  http://www.lexique.org/shiny/lexique/

import argparse
import sqlite3
import pandas as pd
import time
# Adicionando a importação que faltava
import traceback

def main():
    parser = argparse.ArgumentParser(description="Processa a planilha Excel Lexique e a insere em um banco SQLite.")
    parser.add_argument("lexique_file", help="Caminho para a planilha Excel Lexique.")
    parser.add_argument("--output", required=True, help="Arquivo SQLite de saída.")
    args = parser.parse_args()

    TARGET_POS = {"NOM", "ADJ"}

    try:
        conn = sqlite3.connect(args.output)
        cursor = conn.cursor()
        print(f"Banco de dados '{args.output}' aberto/criado com sucesso.")

        # Recriamos a tabela do zero para garantir que não haja dados de tentativas anteriores.
        cursor.execute("DROP TABLE IF EXISTS palavras")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS palavras (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                palavra TEXT NOT NULL,
                classe_gramatical TEXT NOT NULL,
                genero TEXT,
                numero TEXT,
                lema TEXT,
                UNIQUE(palavra, lema, classe_gramatical, genero, numero)
            )
        """)
        conn.commit()
    except sqlite3.Error as e:
        print(f"ERRO CRÍTICO: Não foi possível criar o banco de dados. {e}")
        return

    start_time = time.time()
    try:
        # ETAPA 1: Lendo a planilha com PANDAS.
        print(f"Etapa 1/5: Lendo o arquivo Excel '{args.lexique_file}'...")
        df = pd.read_excel(args.lexique_file, engine='openpyxl')
        print(f"   - Arquivo lido. Total de linhas: {len(df):,}")

        # ETAPA 2: Filtrando para manter apenas NOM e ADJ.
        print("Etapa 2/5: Filtrando para manter apenas substantivos (NOM) e adjetivos (ADJ)...")
        filtered_df = df[df['cgram'].isin(TARGET_POS)].copy()
        print(f"   - Filtro inicial concluído. Registros encontrados: {len(filtered_df):,}")

        # --- NOVA ETAPA DE LIMPEZA ---
        # ETAPA 3: Removendo linhas onde a palavra ou o lema estão vazios.
        print("Etapa 3/5: Limpando dados - removendo registros com palavras ou lemas vazios...")
        # .dropna() remove linhas que contêm valores nulos (NaN) nas colunas especificadas.
        cleaned_df = filtered_df.dropna(subset=['ortho', 'lemme']).copy()
        removidos = len(filtered_df) - len(cleaned_df)
        if removidos > 0:
            print(f"   - Limpeza concluída. {removidos} registros com dados vazios foram removidos.")
        
        # ETAPA 4: Seleção e renomeação das colunas.
        print("Etapa 4/5: Preparando colunas para o banco de dados...")
        colunas_originais = ['ortho', 'cgram', 'genre', 'nombre', 'lemme']
        novos_nomes = ['palavra', 'classe_gramatical', 'genero', 'numero', 'lema']
        final_df = cleaned_df[colunas_originais]
        final_df.columns = novos_nomes
        print("   - Colunas prontas.")
        
        # ETAPA 5: Inserção dos dados no banco de dados.
        print(f"Etapa 5/5: Inserindo {len(final_df):,} registros limpos no banco de dados...")
        final_df.to_sql('palavras', conn, if_exists='append', index=False)
        conn.commit()
        print(f"   - Inserção concluída.")

        total_time = time.time() - start_time
        print("\n" + "="*50)
        print("✅ PROCESSO FINALIZADO COM SUCESSO!")
        print(f"   {len(final_df):,} registros foram adicionados ao banco de dados.")
        print(f"   Tempo total de execução: {total_time:.2f} segundos.")

    except FileNotFoundError:
        print(f"ERRO FATAL: Arquivo '{args.lexique_file}' não encontrado.")
    except KeyError as e:
        print(f"ERRO FATAL: A coluna {e} não foi encontrada na planilha. Verifique o arquivo.")
    except Exception as e:
        print(f"Ocorreu um erro inesperado: {e}")
        # Agora o traceback funcionará
        traceback.print_exc()
    finally:
        if conn:
            conn.close()
            print("Conexão com o banco de dados fechada.")

if __name__ == "__main__":
    main()

# Executar
# python processador_lexique.py "Lexique-query-2025-07-11 15_12_14.xlsx" --output french_words.sqlite

