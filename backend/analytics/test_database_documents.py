
"""Teste estrutural da função de listagem de documentos."""

import inspect

from database import listar_documentos_por_agente


def main():
    assinatura = inspect.signature(listar_documentos_por_agente)

    assert list(assinatura.parameters) == ["agent_id"]

    codigo = inspect.getsource(listar_documentos_por_agente)

    assert "WHERE agent_id = ?" in codigo
    assert "SELECT id, agent_id, filename, filepath, status" in codigo
    assert "ORDER BY id DESC" in codigo

    print("Assinatura da função: OK")
    print("Filtro por agente: OK")
    print("Campos retornados: OK")
    print("Ordenação: OK")
    print("\nTodos os testes passaram!")


if __name__ == "__main__":
    main()
