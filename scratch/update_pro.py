import sys
import os
sys.path.append('backend')
from database import get_connection

def update_db():
    conn = get_connection()
    try:
        conn.execute('ALTER TABLE users ADD COLUMN is_pro INTEGER DEFAULT 0')
        print('Coluna is_pro adicionada com sucesso!')
    except Exception as e:
        print(f'Aviso: {e} (Provavelmente a coluna já existe)')
    
    # Garantir que o seu usuário seja PRO
    conn.execute('UPDATE users SET is_pro=1 WHERE id=2')
    conn.commit()
    conn.close()
    print('Usuário Rodrigo (ID 2) configurado como PRO.')

if __name__ == "__main__":
    update_db()
