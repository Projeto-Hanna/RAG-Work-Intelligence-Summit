
"""Etapa offline: PDF, CSV, XLSX e JSON -> chunks -> embeddings -> ChromaDB.

Execute sempre que os arquivos da pasta base/ mudarem:
    python index.py
"""

import json
import re
from decimal import Decimal, InvalidOperation
from pathlib import Path

import pandas as pd

from langchain_chroma import Chroma
from langchain_community.document_loaders import PyPDFDirectoryLoader
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

from config import CHUNK_OVERLAP, CHUNK_SIZE, PASTA_BASE, PASTA_DB
from embeddings import get_embeddings


EXTENSOES_SUPORTADAS = {".pdf", ".csv", ".xlsx", ".json"}


def criar_db():
    documentos = carregar_documentos()

    print(f"Documentos carregados: {len(documentos)}")

    if not documentos:
        print(f"Nenhum documento compatível encontrado em '{PASTA_BASE}'.")
        return

    chunks = dividir_chunks(documentos)

    print(f"Chunks criados: {len(chunks)}")

    vetorizar_chunks(chunks)


def carregar_documentos():
    documentos = []

    if not PASTA_BASE.exists():
        print(f"Pasta não encontrada: {PASTA_BASE}")
        return documentos

    arquivos = sorted(
        arquivo
        for arquivo in PASTA_BASE.iterdir()
        if arquivo.is_file()
        and not arquivo.is_symlink()
        and arquivo.suffix.lower() in EXTENSOES_SUPORTADAS
    )

    for arquivo in arquivos:
        print(f"Processando: {arquivo.name}")

        try:
            extensao = arquivo.suffix.lower()

            if extensao == ".pdf":
                documentos.extend(carregar_pdf(arquivo))

            elif extensao == ".csv":
                documentos.extend(carregar_csv(arquivo))

            elif extensao == ".xlsx":
                documentos.extend(carregar_xlsx(arquivo))

            elif extensao == ".json":
                documentos.extend(carregar_json(arquivo))

        except Exception as erro:
            print(f"Erro ao processar {arquivo.name}: {erro}")

    return documentos


def carregar_pdf(arquivo):
    carregador = PyPDFDirectoryLoader(
        str(arquivo.parent),
        glob=arquivo.name
    )

    return carregador.load()


def normalizar_numero(valor):
    """Normaliza números em formato brasileiro ou internacional.

    Exemplos:
        1.234,56 -> 1234.56
        1,234.56 -> 1234.56
        123,45   -> 123.45
        123.45   -> 123.45
        1.234    -> 1234 (padrão brasileiro de milhar)

    Valores ambíguos como 1,234 são interpretados como milhares,
    seguindo o padrão brasileiro.
    """

    if not isinstance(valor, str):
        return valor

    texto = valor.strip()

    if not texto:
        return valor

    # Aceita números com sinal e símbolos monetários comuns.
    correspondencia = re.fullmatch(
        r"([+-]?)\s*(?:R\$\s*)?([\d.,]+)",
        texto
    )

    if not correspondencia:
        return valor

    sinal, numero = correspondencia.groups()

    if not re.fullmatch(r"\d[\d.,]*\d|\d", numero):
        return valor

    if "," in numero and "." in numero:
        # O último separador é considerado decimal.
        if numero.rfind(",") > numero.rfind("."):
            numero = numero.replace(".", "")
            numero = numero.replace(",", ".")
        else:
            numero = numero.replace(",", "")

    elif "," in numero:
        partes = numero.split(",")

        if len(partes) == 2 and len(partes[-1]) in (1, 2):
            numero = numero.replace(",", ".")
        else:
            numero = numero.replace(",", "")

    elif "." in numero:
        partes = numero.split(".")

        if len(partes) == 2 and len(partes[-1]) in (1, 2):
            pass  # Ponto decimal.
        else:
            numero = numero.replace(".", "")

    try:
        numero_decimal = Decimal(sinal + numero)

        if not numero_decimal.is_finite():
            return valor

        return format(numero_decimal, "f")

    except InvalidOperation:
        return valor


def formatar_valor(valor):
    """Converte valores de tabelas em texto adequado para o RAG."""

    if pd.isna(valor):
        return ""

    if isinstance(valor, (int, float)):
        return str(valor)

    if isinstance(valor, str):
        return normalizar_numero(valor)

    return str(valor)


def detectar_separador(arquivo):
    """Detecta se o CSV utiliza vírgula ou ponto e vírgula."""

    encodings = ["utf-8-sig", "cp1252", "latin-1"]

    for encoding in encodings:
        try:
            with arquivo.open("r", encoding=encoding) as entrada:
                amostra = entrada.read(8192)

            if not amostra.strip():
                return ";", encoding

            primeira_linha = amostra.splitlines()[0]

            contagem_ponto_virgula = primeira_linha.count(";")
            contagem_virgula = primeira_linha.count(",")

            if contagem_ponto_virgula > contagem_virgula:
                separador = ";"
            else:
                separador = ","

            return separador, encoding

        except UnicodeDecodeError:
            continue

    raise ValueError("Não foi possível identificar a codificação do CSV.")


def dataframe_para_documentos(dataframe, arquivo, planilha=None):
    documentos = []

    colunas = [str(coluna) for coluna in dataframe.columns]

    for indice, linha in dataframe.iterrows():
        campos = []

        for coluna, valor in zip(colunas, linha):
            valor_formatado = formatar_valor(valor)

            if valor_formatado:
                campos.append(f"{coluna}: {valor_formatado}")

        if not campos:
            continue

        conteudo = (
            f"Arquivo: {arquivo.name}\n"
            f"Registro: {indice + 1}\n"
        )

        if planilha:
            conteudo += f"Planilha: {planilha}\n"

        conteudo += "\n".join(campos)

        metadados = {
            "source": arquivo.name,
            "linha": int(indice + 1),
            "tipo": arquivo.suffix.lower().replace(".", ""),
        }

        if planilha:
            metadados["planilha"] = planilha

        documentos.append(
            Document(
                page_content=conteudo,
                metadata=metadados
            )
        )

    return documentos


def carregar_csv(arquivo):
    separador, encoding = detectar_separador(arquivo)

    dataframe = pd.read_csv(
        arquivo,
        sep=separador,
        encoding=encoding,
        dtype=str,
        keep_default_na=False,
        on_bad_lines="warn"
    )

    print(
        f"  CSV: separador '{separador}', "
        f"encoding '{encoding}', "
        f"{len(dataframe)} registros"
    )

    return dataframe_para_documentos(dataframe, arquivo)


def carregar_xlsx(arquivo):
    documentos = []

    planilhas = pd.read_excel(
        arquivo,
        sheet_name=None,
        dtype=object
    )

    for nome_planilha, dataframe in planilhas.items():
        documentos.extend(
            dataframe_para_documentos(
                dataframe,
                arquivo,
                planilha=nome_planilha
            )
        )

    print(f"  XLSX: {len(planilhas)} planilha(s)")

    return documentos


def json_para_texto(dados, prefixo=""):
    """Transforma estruturas JSON em pares de campos e valores."""

    campos = []

    if isinstance(dados, dict):
        for chave, valor in dados.items():
            novo_prefixo = (
                f"{prefixo}.{chave}" if prefixo else str(chave)
            )

            campos.extend(json_para_texto(valor, novo_prefixo))

    elif isinstance(dados, list):
        for indice, valor in enumerate(dados):
            novo_prefixo = f"{prefixo}[{indice}]"
            campos.extend(json_para_texto(valor, novo_prefixo))

    else:
        valor_formatado = formatar_valor(dados)

        if valor_formatado != "":
            campos.append(f"{prefixo}: {valor_formatado}")

    return campos


def carregar_json(arquivo):
    documentos = []

    with arquivo.open("r", encoding="utf-8-sig") as entrada:
        dados = json.load(entrada)

    if isinstance(dados, list):
        registros = dados
    else:
        registros = [dados]

    for indice, registro in enumerate(registros):
        campos = json_para_texto(registro)

        if not campos:
            continue

        conteudo = (
            f"Arquivo: {arquivo.name}\n"
            f"Registro: {indice + 1}\n"
            + "\n".join(campos)
        )

        documentos.append(
            Document(
                page_content=conteudo,
                metadata={
                    "source": arquivo.name,
                    "linha": indice + 1,
                    "tipo": "json",
                }
            )
        )

    print(f"  JSON: {len(documentos)} registros")

    return documentos


def dividir_chunks(documentos):
    separador_documentos = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        length_function=len,
        add_start_index=True
    )

    return separador_documentos.split_documents(documentos)


def vetorizar_chunks(chunks):
    embeddings = get_embeddings()

    # Novo banco separado: preserva o banco original.
    pasta_db_nova = PASTA_DB.parent / "db_reconstruido"

    if pasta_db_nova.exists():
        raise FileExistsError(
            f"A pasta {pasta_db_nova} já existe. "
            "Verifique seu conteúdo antes de continuar."
        )

    Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        persist_directory=str(pasta_db_nova),
        collection_name="langchain"
    )

    print(f"Novo banco vetorial criado em: {pasta_db_nova}")


if __name__ == "__main__":
    criar_db()
