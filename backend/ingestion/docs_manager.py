import os, json
import shutil
from datetime import datetime

class DocsManager:
    def __init__(self):
        self.prov_dir = os.path.join(os.path.dirname(__file__), '..', 'data', 'provfiles')
        os.makedirs(self.prov_dir, exist_ok=True)

    def save_uploaded_files(self, files: list, serie_version: str = None, tags: str = None, description: str = None) -> dict:
        if not serie_version:
            serie_version = f"serie_{datetime.now().strftime('%d%m%y-%H%M%S')}"
        else:
            serie_version = f"serie_{serie_version}" if not serie_version.startswith("serie_") else serie_version

        serie_path = os.path.join(self.prov_dir, serie_version)
        os.makedirs(serie_path, exist_ok=True)
        metadata = []
        errors = []

        for file in files:
            filename = getattr(file, 'filename', None) or getattr(file, 'name', None)
            if not filename:
                errors.append({'file': str(file), 'error': 'No filename detected'})
                continue
            ext = os.path.splitext(filename)[1].lower()
            if ext not in ['.pdf', '.txt', '.csv', '.docx', '.xlsx', '.xls']:
                errors.append({'file': filename, 'error': f'Unsupported file type: {ext}'})
                continue
            file_path = os.path.join(serie_path, filename)
            try:
                if hasattr(file, 'file'):
                    with open(file_path, 'wb') as f:
                        shutil.copyfileobj(file.file, f)
                elif isinstance(file, str) and os.path.exists(file):
                    shutil.copy(file, file_path)
                else:
                    errors.append({'file': filename, 'error': 'Unsupported file object'})
                    continue

                # Validation après écriture
                if os.path.getsize(file_path) == 0:
                    errors.append({'file': filename, 'error': 'File written is empty'})
                    os.remove(file_path)
                    continue

                stat = os.stat(file_path)
                metadata.append({
                    'name': filename,
                    'format': ext,
                    'size_bytes': stat.st_size,
                    'date': datetime.fromtimestamp(stat.st_mtime).isoformat()
                })
            except Exception as e:
                errors.append({'file': filename, 'error': str(e)})
        # Save meta.json if tags/description provided
        if tags or description:
            meta = {'tags': tags, 'description': description, 'created': datetime.now().isoformat()}
            with open(os.path.join(serie_path, 'meta.json'), 'w', encoding='utf-8') as f:
                json.dump(meta, f, ensure_ascii=False, indent=2)
        return {
            'serie_version': serie_version,
            'serie_path': serie_path,
            'files': metadata,
            'errors': errors
        }

    