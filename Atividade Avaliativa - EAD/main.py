from fastapi import FastAPI, HTTPException #HTTPException para exibir as mensagens de retorno no JSON
from pydantic import BaseModel, Field #Utilização para validação de dados
from datetime import datetime 

app_fila = FastAPI()

# Lista para armazenar os clientes na fila
fila = []

#Utilização para validação de dados
class Cliente(BaseModel):
    nome: str = Field(..., max_length=20, description="Nome do cliente deve conter no máximo 20 caracteres.", )
    tipo_atendimento: str = Field(..., pattern="^[NP]$", description="O tipo de atendimento deve ser 'N' (Normal) ou 'P' (Prioritário).")

# Mensagem na tela principal - ENDPOINT GET
@app_fila.get("/")
async def root():
    return {
        "message": "Olá, Bem-vindo ao sistema de gerenciamento de fila!",
    }

# Endpoint POST do cliente
@app_fila.post("/fila")
async def adicionar_cliente(cliente: Cliente):
    novo_cliente = {
        "nome": cliente.nome,
        "tipo_atendimento": "Prioritário" if cliente.tipo_atendimento == "P" else "Normal",
        "data_chegada": datetime.now().isoformat(),
        "posicao": 0,
        "atendido": False
    }

    if cliente.tipo_atendimento == "P":
        posicao_insercao = next(
            (idx + 1 for idx, c in enumerate(fila) if c["tipo_atendimento"] == "Prioritário"),
            0  # Caso não haja clientes prioritários, insere no topo da fila
        )
        fila.insert(posicao_insercao, novo_cliente)

    else:
        fila.append(novo_cliente)

    # Recalcula as posições
    for idx, c in enumerate(fila):
        c["posicao"] = idx + 1

    return {
        "message": f"Cliente {cliente.nome} adicionado à fila com sucesso!",
        "cliente": novo_cliente
    }


# Endpoint GET da fila para verificar os clientes da fila
@app_fila.get("/fila")
async def obter_fila():
    clientes_nao_atendidos = [
        {
            "posição na fila": cliente["posicao"],
            "nome": cliente["nome"],
            "data de chegada": cliente["data_chegada"],
            "tipo de atendimento": cliente["tipo_atendimento"]
        }
        for cliente in fila if not cliente["atendido"]
    ]

    if not clientes_nao_atendidos:
        return {}

    return {
        "message": "Aqui está a lista de clientes esperando na fila:",
        "fila": clientes_nao_atendidos
    }


# Endpoint GET da fila por {id} para filtrar o cliente de acordo com a posição da fila
@app_fila.get("/fila/{id}")
async def obter_cliente(id: int):
    if id <= 0 or id > len(fila):
        raise HTTPException(status_code=404, detail=f"Não há nenhum cliente na posição {id} da fila. Verifique se o número está correto.")
    
    cliente = fila[id - 1]
    return {
        "message": f"Detalhes do cliente na posição {id}:",
        "cliente": {
            "posição na fila": cliente["posicao"],
            "nome": cliente["nome"],
            "data de chegada": cliente["data_chegada"],
            "tipo de atendimento": cliente["tipo_atendimento"]
        }
    }

# Endpoint PUT da fila
@app_fila.put("/fila")
async def atualizar_fila():
    if not fila:
        raise HTTPException(status_code=404, detail="Não há clientes na fila")
    
    for cliente in fila:
        if cliente["posicao"] == 1:
            cliente["posicao"] = 0
            cliente["atendido"] = True
        else:
            cliente["posicao"] -= 1

    fila[:] = [cli for cli in fila if not cli["atendido"]]

    return {"message": "Fila atualizada!", "fila": fila}


# Endpoint DELETE da fila por {id}
@app_fila.delete("/fila/{id}")
async def remover_cliente(id: int):
    if id <= 0 or id > len(fila):
        raise HTTPException(status_code=404, detail="Não foi encontrado um cliente nessa posição.")
    
    cliente_removido = fila.pop(id - 1)

    for idx, cliente in enumerate(fila):
        cliente["posicao"] = idx + 1

    return {
        "message": f"O cliente {cliente_removido['nome']} foi removido da fila.",
        "fila": fila
    }
