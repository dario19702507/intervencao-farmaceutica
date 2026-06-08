from datetime import datetime

ASSINATURA = (
    "\n\n"
    "Farmácia Escola Profa. Ana Maria Cervantes Baraza\n"
    "Universidade Federal de Mato Grosso do Sul (UFMS)\n"
    "Campo Grande - MS"
)


def mensagem_retirada_amanha(nome):
    return (
        f"Olá {nome}.\n\n"
        f"Lembramos que sua retirada de medicamentos está programada para amanhã "
        f"na Farmácia Escola da UFMS.\n\n"
        f"Em caso de dúvidas, entre em contato com nossa equipe."
        f"{ASSINATURA}"
    )

def mensagem_retirada_hoje(nome):
    return (
        f"Olá {nome}.\n\n"
        f"Sua retirada de medicamentos está prevista para hoje "
        f"na Farmácia Escola da UFMS."
        f"{ASSINATURA}"
    )

def mensagem_renovacao(nome):
    return (
        f"Olá {nome}.\n\n"
        f"Identificamos que seu laudo está próximo do vencimento.\n\n"
        f"Procure sua unidade de saúde para providenciar a renovação."
        f"{ASSINATURA}"
    )

def mensagem_risco_interrupcao(nome):
    return (
        f"Olá {nome}.\n\n"
        f"Identificamos risco de interrupção do seu tratamento por ausência de renovação do processo.\n\n"
        f"Procure sua unidade de saúde o mais breve possível."
        f"{ASSINATURA}"
    )
    