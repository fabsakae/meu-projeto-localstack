import json
import random
from random import randint, uniform, choice
from datetime import datetime, timedelta

def random_date():
    today = datetime.now()
    days_ago = randint(1, 30)
    random_date = today - timedelta(days=days_ago)
    return random_date.strftime("%Y-%m-%d")

clientes = ["João Silva", "Maria Oliveira", "Carlos Santos", "Ana Costa", "Pedro Lima"]

registros = []
for i in range(10):
    registro = {
        "Id": f"NF-{i+1}",
        "cliente": choice(clientes),
        "valor": round(uniform(100.0, 5000.0), 2),
        "data_emissao": random_date()
    }
    registros.append(registro)

with open("notas_fiscais.json", "w", encoding="utf-8") as f:
    json.dump(registros, f, indent=4, ensure_ascii=False)

print("Arquivo 'notas_fiscais.json' gerado com sucesso!")
