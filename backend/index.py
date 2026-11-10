
"""Etapa offline: PDF, CSV, XLSX e JSON -> chunks -> embeddings -> ChromaDB.

Execute sempre que os arquivos da pasta base/ mudarem:
    python index.py
"""

import json
import re
import hashlib
from database import (
    cadastrar_agente,
    cadastrar_ou_atualizar_documento,
    registrar_documento,
    atualizar_status_documento,
    obter_tipo_base_agente,
    obter_documento_por_id,

)

from knowledge_base import obter_diretorios_base
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

def criar_db(agent_id: str):
    tipo_base = obter_tipo_base_agente(agent_id)

    if tipo_base == "test":
        cadastrar_agente(
            agent_id="shared_test",
            name="Base Compartilhada de Testes",
            knowledge_base_type="test",
        )

    pasta_base, pasta_db = obter_diretorios_base(agent_id, tipo_base)
    pasta_base.mkdir(parents=True, exist_ok=True)

    arquivos = sorted(
        arquivo for arquivo in pasta_base.iterdir()
        if arquivo.is_file()
        and not arquivo.is_symlink()
        and arquivo.suffix.lower() in EXTENSOES_SUPORTADAS
    )

    if not arquivos:
        print("Nenhum documento encontrado para indexação.")
        return

    agente_documentos_id = "shared_test" if tipo_base == "test" else agent_id
    escopo_base = "shared_test" if tipo_base == "test" else agent_id

    sucessos = 0
    erros = []

    for arquivo in arquivos:
        document_id = None

        try:
            document_id = cadastrar_ou_atualizar_documento(
                agent_id=agente_documentos_id,
                filename=arquivo.name,
                filepath=str(arquivo.resolve()),
                status="processing",
            )

            documentos = carregar_arquivo(arquivo)
            chunks = dividir_chunks(documentos)

            if not chunks:
                raise RuntimeError(
                    f"Nenhum chunk foi gerado para {arquivo.name}."
                )

            vetorizar_chunks(chunks, pasta_db, escopo_base)

            atualizar_status_documento(document_id, "indexed")
            sucessos += 1

            print(f"Documento indexado: {arquivo.name}")

        except Exception as erro:
            if document_id is not None:
                atualizar_status_documento(document_id, "error")

            erros.append((arquivo.name, str(erro)))
            print(f"Erro ao indexar {arquivo.name}: {erro}")

    print("\nResumo da indexação:")
    print(f"Documentos indexados: {sucessos}")
    print(f"Documentos com erro: {len(erros)}")

    if erros:
        detalhes = "\n".join(
            f"- {nome}: {mensagem}" for nome, mensagem in erros
        )
        raise RuntimeError(
            f"Falha ao indexar {len(erros)} documento(s):\n{detalhes}"
        )

    print("Indexação concluída com sucesso.")

def validar_documento_para_indexacao(
    agent_id: str,
    document_id: int,
) -> tuple[Path, Path, str]:
    """Valida se o documento existe e pertence à pasta autorizada do agente."""

    tipo_base = obter_tipo_base_agente(agent_id)

    agente_documentos_id = (
        "shared_test" if tipo_base == "test" else agent_id
    )

    pasta_base, pasta_db = obter_diretorios_base(
        agent_id,
        tipo_base,
    )

    documento = obter_documento_por_id(
        agente_documentos_id,
        document_id,
    )

    if documento is None:
        raise ValueError("Documento não encontrado.")

    arquivo = Path(documento["filepath"])

    # Valida o caminho e impede acesso fora da pasta documental.
    pasta_base_resolvida = pasta_base.resolve()

    if arquivo.is_symlink():
        raise ValueError("Não é permitido indexar links simbólicos.")

    arquivo_resolvido = arquivo.resolve()

    if arquivo_resolvido.parent != pasta_base_resolvida:
        raise ValueError("Caminho do documento inválido.")

    if not arquivo_resolvido.is_file():
        raise FileNotFoundError("Arquivo não encontrado.")

    if arquivo_resolvido.suffix.lower() not in EXTENSOES_SUPORTADAS:
        raise ValueError("Extensão de arquivo não suportada.")

    return arquivo_resolvido, pasta_db, agente_documentos_id


def executar_indexacao_documento(
    document_id: int,
    arquivo_resolvido: Path,
    pasta_db: Path,
    escopo_base: str,
):
    """Executa a extração, chunking e vetorização atualizando o status no SQLite."""

    try:
        documentos = carregar_arquivo(arquivo_resolvido)
        chunks = dividir_chunks(documentos)

        if not chunks:
            raise RuntimeError("Nenhum chunk foi gerado.")

        vetorizar_chunks(
            chunks,
            pasta_db,
            escopo_base,
        )

        atualizar_status_documento(document_id, "indexed")

        return {
            "message": "Documento indexado com sucesso.",
            "document_id": document_id,
            "status": "indexed",
        }

    except Exception as erro:
        print(f"Erro ao indexar documento {document_id}: {erro}")
        atualizar_status_documento(document_id, "error")
        raise


def indexar_documento(agent_id: str, document_id: int):
    """Indexa individualmente um documento cadastrado."""

    arquivo_resolvido, pasta_db, escopo_base = (
        validar_documento_para_indexacao(agent_id, document_id)
    )

    atualizar_status_documento(document_id, "processing")

    return executar_indexacao_documento(
        document_id=document_id,
        arquivo_resolvido=arquivo_resolvido,
        pasta_db=pasta_db,
        escopo_base=escopo_base,
    )


def remover_documento_vetorizado(
    pasta_db: Path,
    nome_fonte: str,
    escopo_base: str,
):
    """Remove os vetores de um arquivo excluído do ChromaDB."""

    if not (pasta_db / "chroma.sqlite3").is_file():
        return

    embeddings = get_embeddings()

    db = Chroma(
        persist_directory=str(pasta_db),
        embedding_function=embeddings,
        collection_name="langchain",
    )

    filtro = {
        "$and": [
            {"source": {"$eq": nome_fonte}},
            {"base_scope": {"$eq": escopo_base}},
        ]
    }

    db.delete(where=filtro)

    from retriever import carregar_db

    carregar_db.cache_clear()

def carregar_arquivo(arquivo: Path):
    """Carrega individualmente um arquivo compatível."""

    print(f"Processando: {arquivo.name}")

    extensao = arquivo.suffix.lower()

    try:
        if extensao == ".pdf":
            documentos = carregar_pdf(arquivo)

        elif extensao == ".csv":
            documentos = carregar_csv(arquivo)

        elif extensao == ".xlsx":
            documentos = carregar_xlsx(arquivo)

        elif extensao == ".json":
            documentos = carregar_json(arquivo)

        else:
            raise ValueError(
                f"Extensão não suportada: {extensao}"
            )

        if not documentos:
            raise RuntimeError(
                f"Nenhum conteúdo foi extraído de {arquivo.name}."
            )

        return documentos

    except Exception as erro:
        raise RuntimeError(
            f"Erro ao processar {arquivo.name}: {erro}"
        ) from erro


def carregar_documentos(pasta_base: Path):
    """Carrega todos os documentos compatíveis de uma pasta."""

    documentos = []

    if not pasta_base.exists():
        print(f"Pasta não encontrada: {pasta_base}")
        return documentos

    arquivos = sorted(
        arquivo
        for arquivo in pasta_base.iterdir()
        if arquivo.is_file()
        and not arquivo.is_symlink()
        and arquivo.suffix.lower() in EXTENSOES_SUPORTADAS
    )

    for arquivo in arquivos:
        documentos.extend(carregar_arquivo(arquivo))

    return documentos


def carregar_pdf(arquivo):
    carregador = PyPDFDirectoryLoader(
        str(arquivo.parent),
        glob=arquivo.name
    )

    documentos = carregador.load()

    for documento in documentos:
        documento.metadata["source"] = arquivo.name
        documento.metadata["tipo"] = "pdf"

    return documentos


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

    chunks = separador_documentos.split_documents(documentos)

    for chunk in chunks:
        source = chunk.metadata.get("source", "desconhecido")
        start_index = chunk.metadata.get("start_index", 0)

        chunk.metadata["chunk_id"] = (
            f"{source}:{start_index}"
        )

    return chunks


def vetorizar_chunks(chunks, pasta_db: Path, escopo_base: str):
    from collections import defaultdict

    embeddings = get_embeddings()

    pasta_db.mkdir(parents=True, exist_ok=True)

    db = Chroma(
        persist_directory=str(pasta_db),
        embedding_function=embeddings,
        collection_name="langchain",
    )

    # Adiciona o escopo aos metadados.
    for chunk in chunks:
        chunk.metadata["base_scope"] = escopo_base

    # Agrupa os chunks por arquivo.
    chunks_por_fonte = defaultdict(list)

    for chunk in chunks:
        fonte = chunk.metadata["source"]
        chunks_por_fonte[fonte].append(chunk)

    for fonte, chunks_fonte in chunks_por_fonte.items():
        print(f"Atualizando: {fonte}")

        filtro = {
            "$and": [
                {"source": {"$eq": fonte}},
                {"base_scope": {"$eq": escopo_base}},
            ]
        }

        # Gera os IDs dos novos chunks.
        ids = []

        for chunk in chunks_fonte:
            identificador = {
                "metadata": chunk.metadata,
                "content": chunk.page_content,
            }

            conteudo_id = json.dumps(
                identificador,
                ensure_ascii=False,
                sort_keys=True,
                default=str,
            )

            ids.append(
                hashlib.sha256(
                    conteudo_id.encode("utf-8")
                ).hexdigest()
            )

        # Calcula os embeddings antes de modificar a base.
        vetores = embeddings.embed_documents(
            [chunk.page_content for chunk in chunks_fonte]
        )

        # Recupera os registros antigos para backup.
        backup = db.get(
            where=filtro,
            include=["embeddings", "documents", "metadatas"],
        )

        try:
            # Remove os registros antigos do arquivo e escopo.
            db.delete(where=filtro)

            # Insere os novos registros.
            db._collection.upsert(
                ids=ids,
                embeddings=vetores,
                documents=[
                    chunk.page_content for chunk in chunks_fonte
                ],
                metadatas=[
                    chunk.metadata for chunk in chunks_fonte
                ],
            )

            print(f"Arquivo atualizado: {fonte}")

        except Exception as erro:
            print(f"Erro ao atualizar {fonte}. Tentando restaurar backup...")

            try:
                # Remove possíveis registros inseridos parcialmente.
                db.delete(where=filtro)

                # Restaura os registros anteriores.
                if backup["ids"]:
                    db._collection.upsert(
                        ids=backup["ids"],
                        embeddings=backup["embeddings"],
                        documents=backup["documents"],
                        metadatas=backup["metadatas"],
                    )

                print(f"Backup restaurado: {fonte}")

            except Exception as erro_restauracao:
                raise RuntimeError(
                    f"Falha ao atualizar '{fonte}' e também ao "
                    f"restaurar o backup. Erro original: {erro}. "
                    f"Erro na restauração: {erro_restauracao}"
                ) from erro_restauracao

            raise RuntimeError(
                f"Falha ao atualizar '{fonte}'. "
                "Os registros anteriores foram restaurados."
            ) from erro

    from retriever import carregar_db

    carregar_db.cache_clear()

    print(f"Banco vetorial atualizado em: {pasta_db}")

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Indexa documentos na base de conhecimento de um agente."
    )

    parser.add_argument(
        "agent_id",
        help="Identificador do agente que receberá a indexação.",
    )

    args = parser.parse_args()

    criar_db(args.agent_id)
