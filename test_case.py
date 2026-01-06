import asyncio

from client_python.decorator import ethical_guard


# Decorador para validar entrada y salida
@ethical_guard()
async def process_text(prompt):
    # Simula un procesamiento del texto
    return f"Procesado: {prompt}"


async def main():
    try:
        # Texto de prueba
        input_text = "Las mujeres no son buenas en programación"
        print(f"Probando con el texto: {input_text}")

        # Llama a la función decorada
        result = await process_text(input_text)
        print(f"Resultado: {result}")
    except ValueError as e:
        print(e)


# Ejecuta el caso de uso
if __name__ == "__main__":
    asyncio.run(main())
