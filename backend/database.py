"""Persistência de metadados do AgentLab."""

import sqlite3

from config import ARQUIVO_DATABASE


def conectar():
    ARQUIVO_DATABASE.parent.mkdir(parents=True, exist_ok=True)

    conexao = sqlite3.connect(ARQUIVO_DATABASE)
    conexao.row_factory = sqlite3.Row
    conexao.execute("PRAGMA foreign_keys = ON")

    return conexao


def inicializar_banco():
    with conectar() as conexao:
        conexao.executescript("""
            CREATE TABLE IF NOT EXISTS agents (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                knowledge_base_type TEXT NOT NULL
                    CHECK (knowledge_base_type IN ('test', 'custom')),
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS documents (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                agent_id TEXT NOT NULL,
                filename TEXT NOT NULL,
                filepath TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'uploaded',
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (agent_id) REFERENCES agents(id)
            );

            CREATE TABLE IF NOT EXISTS training_examples (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                agent_id TEXT NOT NULL,
                question TEXT NOT NULL,
                answer TEXT NOT NULL,
                approved INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (agent_id) REFERENCES agents(id)
            );
        """)


if __name__ == "__main__":
    inicializar_banco()
    print("Banco de metadados inicializado.")
    
def cadastrar_agente(agent_id: str, name: str, knowledge_base_type: str):
    with conectar() as conexao:
        conexao.execute(
            """
            INSERT INTO agents (id, name, knowledge_base_type)
            VALUES (?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                name = excluded.name,
                knowledge_base_type = excluded.knowledge_base_type
            """,
            (agent_id, name, knowledge_base_type),
        )
        
def obter_tipo_base_agente(agent_id: str) -> str:
    with conectar() as conexao:
        resultado = conexao.execute(
            """
            SELECT knowledge_base_type
            FROM agents
            WHERE id = ?
            """,
            (agent_id,),
        ).fetchone()

    if resultado is None:
        raise ValueError("Agente não encontrado.")

    return resultado["knowledge_base_type"]


def registrar_documento(
    agent_id: str,
    filename: str,
    filepath: str,
    status: str = "uploaded",
) -> int:
    with conectar() as conexao:
        cursor = conexao.execute(
            """
            INSERT INTO documents (
                agent_id,
                filename,
                filepath,
                status
            )
            VALUES (?, ?, ?, ?)
            """,
            (agent_id, filename, filepath, status),
        )

        return cursor.lastrowid


def atualizar_status_documento(
    document_id: int,
    status: str,
):
    with conectar() as conexao:
        conexao.execute(
            """
            UPDATE documents
            SET status = ?
            WHERE id = ?
            """,
            (status, document_id),
        )
        

def obter_documento(agent_id: str, filename: str):
    with conectar() as conexao:
        resultado = conexao.execute(
            """
            SELECT id, agent_id, filename, filepath, status
            FROM documents
            WHERE agent_id = ? AND filename = ?
            ORDER BY id DESC
            LIMIT 1
            """,
            (agent_id, filename),
        ).fetchone()

    return resultado

def obter_documento_por_id(agent_id: str, document_id: int):
    """Busca um documento pelo ID, respeitando o agente proprietário."""

    with conectar() as conexao:
        resultado = conexao.execute(
            """
            SELECT id, agent_id, filename, filepath, status
            FROM documents
            WHERE id = ? AND agent_id = ?
            """,
            (document_id, agent_id),
        ).fetchone()

    return resultado

def cadastrar_ou_atualizar_documento(
    agent_id: str,
    filename: str,
    filepath: str,
    status: str = "uploaded",
) -> int:
    with conectar() as conexao:
        resultado = conexao.execute(
            """
            SELECT id
            FROM documents
            WHERE agent_id = ? AND filename = ?
            ORDER BY id DESC
            LIMIT 1
            """,
            (agent_id, filename),
        ).fetchone()

        if resultado:
            document_id = resultado["id"]

            conexao.execute(
                """
                UPDATE documents
                SET filepath = ?, status = ?
                WHERE id = ?
                """,
                (filepath, status, document_id),
            )

            return document_id

        cursor = conexao.execute(
            """
            INSERT INTO documents (
                agent_id, filename, filepath, status
            )
            VALUES (?, ?, ?, ?)
            """,
            (agent_id, filename, filepath, status),
        )

        return cursor.lastrowid