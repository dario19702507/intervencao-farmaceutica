from datetime import datetime, time, timedelta


HORARIOS_FARMACIA = {
    0: [(time(13, 30), time(16, 30))],  # segunda
    1: [(time(7, 30), time(11, 0))],    # terça
    2: [(time(7, 30), time(11, 0))],    # quarta
    3: [(time(7, 30), time(11, 0)), (time(13, 30), time(16, 30))],  # quinta
}


def esta_em_horario_atendimento(data_hora: datetime) -> bool:
    periodos = HORARIOS_FARMACIA.get(data_hora.weekday(), [])

    for inicio, fim in periodos:
        if inicio <= data_hora.time() <= fim:
            return True

    return False


def ajustar_para_proximo_horario_atendimento(data_hora: datetime) -> datetime:
    data_base = data_hora

    for dias_a_frente in range(0, 14):
        candidato_data = data_base.date() + timedelta(days=dias_a_frente)
        weekday = candidato_data.weekday()
        periodos = HORARIOS_FARMACIA.get(weekday, [])

        for inicio, fim in periodos:
            candidato = datetime.combine(candidato_data, inicio)

            if candidato >= data_hora:
                return candidato

            if datetime.combine(candidato_data, inicio) <= data_hora <= datetime.combine(candidato_data, fim):
                return data_hora

    # fallback seguro
    proxima_segunda = data_hora + timedelta(days=(7 - data_hora.weekday()) % 7)
    return datetime.combine(proxima_segunda.date(), time(13, 30))


def descrever_horarios_farmacia() -> dict:
    return {
        "segunda": ["13:30-16:30"],
        "terca": ["07:30-11:00"],
        "quarta": ["07:30-11:00"],
        "quinta": ["07:30-11:00", "13:30-16:30"],
        "sexta": [],
        "sabado": [],
        "domingo": [],
    }