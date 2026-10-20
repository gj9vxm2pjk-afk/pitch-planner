"""Google Sheets/Drive access with a service account, shared by refresh.py and sync_tables.py.

Credentials: key JSON in $GOOGLE_SERVICE_ACCOUNT_JSON, or a file path in $GOOGLE_APPLICATION_CREDENTIALS.
Needs: pip install google-auth requests
Every helper exits with a "FAILED: ..." message on error, so callers never carry on with partial data.
"""
import json, os, sys
from urllib.parse import quote

SHEET_IDS = {
    'latest':   '1Maux72-4AZUgkoHtkJZOQbU7rpPlA3d339fKg8Srffo',  # WBR Age Grade Fixtures 26/27 (old grid sheet)
    'bookings': '1QAic2QwRDZUJHRQ7LHZVqVxrh-IdjqNMpTyos6FMKnE',  # WBR Paddock & Scrum Machine Bookings
    'training': '1J8sPyVbvGTNKMwhkA0R6S07qbQBXOm0LY5cvXeNRxrY',  # WBR Training Schedule
    'table':    '',                                              # new table-format fixtures sheet (set when it exists)
}
READ = ['https://www.googleapis.com/auth/drive.readonly']
WRITE = READ + ['https://www.googleapis.com/auth/spreadsheets']
SHEETS = 'https://sheets.googleapis.com/v4/spreadsheets'

def session(write=False):
    """An authorised HTTP session, or None when no service account is configured."""
    creds_json = os.environ.get('GOOGLE_SERVICE_ACCOUNT_JSON', '').strip()
    creds_file = os.environ.get('GOOGLE_APPLICATION_CREDENTIALS', '').strip()
    if not (creds_json or creds_file):
        return None
    try:
        from google.oauth2 import service_account
        from google.auth.transport.requests import AuthorizedSession
        scopes = WRITE if write else READ
        creds = (service_account.Credentials.from_service_account_info(json.loads(creds_json), scopes=scopes)
                 if creds_json else service_account.Credentials.from_service_account_file(creds_file, scopes=scopes))
        return AuthorizedSession(creds)
    except Exception as e:
        sys.exit(f'FAILED: could not set up the Google service account ({type(e).__name__}: {e})')

def _call(sess, method, url, label, **kw):
    try:
        r = getattr(sess, method)(url, timeout=60, **kw)
    except Exception as e:
        sys.exit(f'FAILED: could not reach Google for {label} ({type(e).__name__}: {e})')
    if r.status_code != 200:
        sys.exit(f'FAILED: Google returned HTTP {r.status_code} for {label} (is the sheet shared with the service account?)')
    return r

def export_csv(sess, sheet_id, label):
    """CSV text of the first tab of a sheet (Drive export endpoint)."""
    r = _call(sess, 'get', f'https://www.googleapis.com/drive/v3/files/{sheet_id}/export', f'the {label} sheet',
              params={'mimeType': 'text/csv'})
    return r.content.decode('utf-8-sig')

def get_values(sess, sheet_id, rng, label):
    """Rows (lists of strings) in a range such as "Config!A1:B10"."""
    r = _call(sess, 'get', f'{SHEETS}/{sheet_id}/values/{quote(rng, safe="")}', f'{label} ({rng})',
              params={'valueRenderOption': 'FORMATTED_VALUE'})
    return r.json().get('values', [])

def clear_values(sess, sheet_id, rng, label):
    _call(sess, 'post', f'{SHEETS}/{sheet_id}/values/{quote(rng, safe="")}:clear', f'{label} ({rng})', json={})

def put_values(sess, sheet_id, rng, values, label):
    """Write values as plain text (RAW), leaving the sheet's dropdowns and formatting alone."""
    _call(sess, 'put', f'{SHEETS}/{sheet_id}/values/{quote(rng, safe="")}', f'{label} ({rng})',
          params={'valueInputOption': 'RAW'}, json={'range': rng, 'majorDimension': 'ROWS', 'values': values})
