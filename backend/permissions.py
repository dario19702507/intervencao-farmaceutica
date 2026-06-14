"""Controle centralizado de permissões por perfil.

Este módulo concentra a política de autorização do sistema para evitar regras
espalhadas entre routers. As funções recebem um objeto de usuário SQLAlchemy
ou equivalente, desde que possua os atributos ``perfil`` e
``categoria_profissional``.
"""
from typing import Iterable, Optional

from fastapi import HTTPException


PERFIL_ADMIN = "admin"
PERFIL_FARMACEUTICO = "farmaceutico"
PERFIL_ESTAGIARIO = "estagiario"
PERFIL_PESQUISADOR = "pesquisador"
PERFIL_VISUALIZACAO = "visualizacao"

# Compatibilidade com versões anteriores do sistema.
PERFIL_LEITOR_LEGADO = "leitor"
PERFIL_OPERADOR_LEGADO = "operador"

PERFIS_VALIDOS = {
    PERFIL_ADMIN,
    PERFIL_FARMACEUTICO,
    PERFIL_ESTAGIARIO,
    PERFIL_PESQUISADOR,
    PERFIL_VISUALIZACAO,
    PERFIL_LEITOR_LEGADO,
    PERFIL_OPERADOR_LEGADO,
}

CATEGORIAS_REGISTRO_ASSISTENCIAL = {
    "Farmacêutico",
    "Docente",
    "Residente",
    "Estagiário",
    "Técnico",
}

CATEGORIAS_RESPONSAVEL_CLINICO = {
    "Farmacêutico",
    "Docente",
}

PERFIS_ESCRITA = {
    PERFIL_ADMIN,
    PERFIL_FARMACEUTICO,
    PERFIL_ESTAGIARIO,
    PERFIL_OPERADOR_LEGADO,
}

PERFIS_LEITURA_RESTRITA = {
    PERFIL_VISUALIZACAO,
    PERFIL_PESQUISADOR,
    PERFIL_LEITOR_LEGADO,
}


MODULOS_SISTEMA = [
    "intervencoes",
    "consultorio",
    "documentos",
    "relatorios",
    "agenda",
    "administracao",
]

PERMISSOES_POR_PERFIL = {
    PERFIL_ADMIN: {
        "intervencoes": {"ver": True, "editar": True},
        "consultorio": {"ver": True, "editar": True},
        "documentos": {"ver": True, "editar": True},
        "relatorios": {"ver": True, "editar": False},
        "agenda": {"ver": True, "editar": True},
        "administracao": {"ver": True, "editar": True},
    },
    PERFIL_FARMACEUTICO: {
        "intervencoes": {"ver": True, "editar": True},
        "consultorio": {"ver": True, "editar": True},
        "documentos": {"ver": True, "editar": True},
        "relatorios": {"ver": True, "editar": False},
        "agenda": {"ver": True, "editar": True},
        "administracao": {"ver": False, "editar": False},
    },
    PERFIL_ESTAGIARIO: {
        "intervencoes": {"ver": True, "editar": True},
        "consultorio": {"ver": True, "editar": True},
        "documentos": {"ver": True, "editar": False},
        "relatorios": {"ver": True, "editar": False},
        "agenda": {"ver": True, "editar": False},
        "administracao": {"ver": False, "editar": False},
    },
    PERFIL_PESQUISADOR: {
        "intervencoes": {"ver": True, "editar": False},
        "consultorio": {"ver": True, "editar": False},
        "documentos": {"ver": False, "editar": False},
        "relatorios": {"ver": True, "editar": False},
        "agenda": {"ver": False, "editar": False},
        "administracao": {"ver": False, "editar": False},
    },
    PERFIL_VISUALIZACAO: {
        "intervencoes": {"ver": True, "editar": False},
        "consultorio": {"ver": True, "editar": False},
        "documentos": {"ver": True, "editar": False},
        "relatorios": {"ver": True, "editar": False},
        "agenda": {"ver": True, "editar": False},
        "administracao": {"ver": False, "editar": False},
    },
}


def obter_permissoes_modulos(perfil: Optional[str]) -> dict:
    """Retorna a matriz de permissões por módulo para um perfil do cadastro único."""
    perfil_normalizado = normalizar_perfil(perfil)
    base = PERMISSOES_POR_PERFIL.get(perfil_normalizado)
    if not base:
        # Perfis legados seguem a regra mais conservadora compatível.
        if perfil_normalizado == PERFIL_OPERADOR_LEGADO:
            base = PERMISSOES_POR_PERFIL[PERFIL_FARMACEUTICO]
        elif perfil_normalizado == PERFIL_LEITOR_LEGADO:
            base = PERMISSOES_POR_PERFIL[PERFIL_VISUALIZACAO]
        else:
            base = PERMISSOES_POR_PERFIL[PERFIL_VISUALIZACAO]

    return {
        modulo: {
            "ver": bool(base.get(modulo, {}).get("ver", False)),
            "editar": bool(base.get(modulo, {}).get("editar", False)),
        }
        for modulo in MODULOS_SISTEMA
    }


def normalizar_perfil(perfil: Optional[str]) -> str:
    """Normaliza perfis antigos e novos para comparação."""
    valor = (perfil or "").strip().lower()
    aliases = {
        "administrador": PERFIL_ADMIN,
        "farmacêutico": PERFIL_FARMACEUTICO,
        "farmaceutico": PERFIL_FARMACEUTICO,
        "estudante": PERFIL_ESTAGIARIO,
        "estagiário": PERFIL_ESTAGIARIO,
        "estagiario": PERFIL_ESTAGIARIO,
        "leitura": PERFIL_VISUALIZACAO,
        "visualização": PERFIL_VISUALIZACAO,
        "visualizacao": PERFIL_VISUALIZACAO,
    }
    return aliases.get(valor, valor)


def obter_perfil(user) -> str:
    return normalizar_perfil(getattr(user, "perfil", None))


def obter_categoria(user) -> str:
    return (getattr(user, "categoria_profissional", None) or "").strip()


def exigir_autenticado(user):
    if not user:
        raise HTTPException(status_code=401, detail="Usuário não autenticado")
    return user


def exigir_admin(user):
    exigir_autenticado(user)
    if obter_perfil(user) != PERFIL_ADMIN:
        raise HTTPException(status_code=403, detail="Acesso restrito ao administrador")
    return user


def exigir_perfil(user, perfis_permitidos: Iterable[str]):
    exigir_autenticado(user)
    permitidos = {normalizar_perfil(p) for p in perfis_permitidos}
    if obter_perfil(user) not in permitidos:
        raise HTTPException(status_code=403, detail="Perfil sem permissão para esta ação")
    return user


def exigir_pode_registrar(user):
    exigir_autenticado(user)
    perfil = obter_perfil(user)
    categoria = obter_categoria(user)

    if perfil in PERFIS_ESCRITA:
        return user

    if categoria in CATEGORIAS_REGISTRO_ASSISTENCIAL:
        return user

    raise HTTPException(status_code=403, detail="Usuário sem permissão para registrar dados")


def exigir_pode_escrever(user):
    exigir_autenticado(user)
    if obter_perfil(user) in PERFIS_LEITURA_RESTRITA:
        raise HTTPException(status_code=403, detail="Perfil sem permissão para alterar registros")
    return user


def exigir_farmaceutico_ou_admin(user):
    exigir_autenticado(user)
    perfil = obter_perfil(user)
    categoria = obter_categoria(user)

    if perfil == PERFIL_ADMIN:
        return user

    if categoria in CATEGORIAS_RESPONSAVEL_CLINICO:
        return user

    raise HTTPException(
        status_code=403,
        detail="Ação permitida apenas para farmacêutico, docente ou administrador",
    )


def usuario_eh_leitura_restrita(user) -> bool:
    return obter_perfil(user) in PERFIS_LEITURA_RESTRITA


def validar_perfil_usuario(perfil: str) -> str:
    perfil_normalizado = normalizar_perfil(perfil)
    if perfil_normalizado not in PERFIS_VALIDOS:
        raise HTTPException(status_code=400, detail="Perfil inválido")
    return perfil_normalizado
