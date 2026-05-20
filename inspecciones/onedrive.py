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
        authority="https://login.microsoftonline.com/" + TENANT_ID,
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
        'Authorization': 'Bearer ' + token,
        'Content-Type': 'application/octet-stream',
    }

    url = (
        "https://graph.microsoft.com/v1.0/me/drive/root:/"
        + FOLDER_NAME + "/" + nombre_archivo + ":/content"
    )

    resp = requests.put(url, headers=headers, data=contenido_bytes)
    resp.raise_for_status()
    data = resp.json()
    return data.get('webUrl', '')


def eliminar_foto_onedrive(nombre_archivo):
    token = _get_token()
    if not token:
        return

    headers = {'Authorization': 'Bearer ' + token}
    url = (
        "https://graph.microsoft.com/v1.0/me/drive/root:/"
        + FOLDER_NAME + "/" + nombre_archivo
    )
    requests.delete(url, headers=headers)