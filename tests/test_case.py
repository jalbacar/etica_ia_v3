import asyncio
import sys
from pathlib import Path

# Agregar el directorio raíz del proyecto al PYTHONPATH
project_root = Path(__file__).resolve().parents[2]
sys.path.append(str(project_root))

import sys
from pathlib import Path

# Agregar el directorio raíz del proyecto al PYTHONPATH
project_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(project_root))

from client_python.decorator import ethical_guard


# Decorador para validar entrada y salida
@ethical_guard()
async def process_text(prompt):
    # Simula un procesamiento del texto
    return f"Procesado: {prompt}"


async def main():
    try:
        # Texto de prueba
        input_text = "Los hombres son mejores líderes que las mujeres"
        print(f"Probando con el texto: {input_text}")

        # Llama a la función decorada
        result = await process_text(input_text)
        print(f"Resultado: {result}")
    except ValueError as e:
        print(e)


# Ejecuta el caso de uso
if __name__ == "__main__":
    asyncio.run(main())
