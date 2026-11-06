import os
import json
from urllib.parse import urlparse, parse_qs
from http.server import BaseHTTPRequestHandler
from google.oauth2 import service_account
from googleapiclient.discovery import build

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        # 1. Pega o ID da pasta que o botão clicou
        query = parse_qs(urlparse(self.path).query)
        folder_id = query.get('folder', [''])[0]

        if not folder_id:
            self.send_response(400)
            self.end_headers()
            self.wfile.write(json.dumps({"erro": "Faltou o ID da pasta"}).encode('utf-8'))
            return

        try:
            # 2. Autenticação com as chaves da Vercel
            client_email = os.environ.get('GOOGLE_DRIVE_CLIENT_EMAIL')
            private_key = os.environ.get('GOOGLE_DRIVE_PRIVATE_KEY', '').replace('\\n', '\n')

            credentials_info = {
                "client_email": client_email,
                "private_key": private_key,
                "token_uri": "https://oauth2.googleapis.com/token",
            }
            
            creds = service_account.Credentials.from_service_account_info(
                credentials_info, scopes=['https://www.googleapis.com/auth/drive.readonly']
            )

            drive_service = build('drive', 'v3', credentials=creds)

            # 3. Busca as fotos na pasta
            results = drive_service.files().list(
                q=f"'{folder_id}' in parents and mimeType contains 'image/'",
                fields="files(id, name, thumbnailLink)"
            ).execute()

            fotos = results.get('files', [])

            # 4. Devolve as fotos para a tela
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(fotos).encode('utf-8'))

        except Exception as e:
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"erro": str(e)}).encode('utf-8'))
