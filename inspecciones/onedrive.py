import os
import requests
import msal

TENANT_ID     = os.environ.get('AZURE_TENANT_ID')
CLIENT_ID     = os.environ.get('AZURE_CLIENT_ID')
CLIENT_SECRET = os.environ.get('AZURE_CLIENT_SECRET')
FOLDER_NAME   = os.environ.get('ONEDRIVE_FOLDER', 'medidores-fotos')

def _get_token():
    app = msal.ConfidentialClientApplication(
        CLIENT_ID,
        authority=f"https://login.microsoftonline.com/{TENANT_ID}",
        client_credential=CLIENT_SECRET,
    )
    result = app.acquire_token_for_client(
        scopes=["https://graph.microsoft.com/.default"]
    )
    return result.get('access_token')

def subir_foto_onedrive(nombre_archivo, contenido_bytes):
    token = _get_token()
    if not token:
        raise Exception("No se pudo obtener token de Azure")

    headers = {
        'Authorization': f'Bearer {token}',