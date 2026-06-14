import time
import requests


def test_agenda_opcoes(api_url, auth_headers):
    response = requests.get(f"{api_url}/consultorio/agenda/opcoes", headers=auth_headers, timeout=20)
    assert response.status_code == 200, response.text
    data = response.json()
    assert "INCLUSAO" in data["tipos_evento"]
    assert "RETIRADA" in data["tipos_evento"]
    assert "URGENTE" in data["prioridades"]


def test_catalogo_medicamentos_crud_basico(api_url, auth_headers):
    sufixo = int(time.time())
    payload = {
        "farmaco": f"Teste Farmaco {sufixo}",
        "apresentacao": "Comprimido",
        "concentracao": "10 mg",
        "forma_farmaceutica": "Comprimido",
        "componente": "Teste",
        "frequencia_dispensacao": "MENSAL",
    }

    criado = requests.post(f"{api_url}/consultorio/catalogo-medicamentos", json=payload, headers=auth_headers, timeout=20)
    assert criado.status_code == 200, criado.text
    medicamento_id = criado.json()["medicamento"]["id"]

    lista = requests.get(f"{api_url}/consultorio/catalogo-medicamentos?busca={payload['farmaco']}", headers=auth_headers, timeout=20)
    assert lista.status_code == 200, lista.text
    assert lista.json()["total"] >= 1

    atualizado = requests.put(
        f"{api_url}/consultorio/catalogo-medicamentos/{medicamento_id}",
        json={"observacoes": "Atualizado pelo teste automatizado"},
        headers=auth_headers,
        timeout=20,
    )
    assert atualizado.status_code == 200, atualizado.text

    inativado = requests.delete(f"{api_url}/consultorio/catalogo-medicamentos/{medicamento_id}", headers=auth_headers, timeout=20)
    assert inativado.status_code == 200, inativado.text
