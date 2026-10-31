"""TIKILENS VN - Tai CausaSent ATE v2 qua 3 file goc, tranh API /rows 429.

Chi truy cap file cong khai Hugging Face; KHONG truy cap MongoDB Atlas.
Yeu cau: py -m pip install requests
"""
from __future__ import annotations

import hashlib
import json
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

try:
    import requests
except ImportError:
    print('THIEU THU VIEN requests. Chay: py -m pip install requests')
    sys.exit(1)

DATASET_ID = 'Tamir39/causasent-ate-v2'
BASE_URL = 'https://huggingface.co/datasets/Tamir39/causasent-ate-v2'
FOLDER = Path(__file__).resolve().parent / 'tikilens_source2'
OUTPUT = FOLDER / 'causasent_ate_v2.jsonl'
MANIFEST = FOLDER / 'source_manifest.json'
SPLITS = ('train', 'val', 'test')
EXPECTED = {'train': 5647, 'val': 700, 'test': 719}


def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda: f.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def validate(path: Path, split: str) -> list[dict]:
    try:
        with path.open('r', encoding='utf-8-sig') as f:
            records = json.load(f)
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise ValueError(f'{split}.json khong phai JSON hop le: {exc}') from exc
    if not isinstance(records, list):
        raise ValueError(f'{split}.json khong phai danh sach ban ghi.')
    required = {'id', 'source', 'review', 'annotations'}
    for i, item in enumerate(records, start=1):
        if not isinstance(item, dict) or not required.issubset(item):
            raise ValueError(f'{split}.json ban ghi thu {i} thieu truong bat buoc.')
        if not isinstance(item['annotations'], list):
            raise ValueError(f'{split}.json ban ghi thu {i} annotations khong phai list.')
    return records


def download(session: requests.Session, split: str) -> Path:
    url = f'{BASE_URL}/resolve/main/{split}.json'
    final = FOLDER / f'{split}.json'
    pending = FOLDER / f'{split}.json.download'

    # File da hoan tat thi tai su dung, khong gui them request.
    if final.exists():
        try:
            rows = validate(final, split)
            if len(rows) == EXPECTED[split]:
                print(f'  {split}: dung file da tai ({len(rows)} dong).')
                return final
        except (ValueError, OSError):
            pass

    print(f'  Dang tai {split}.json (mot yeu cau HTTP)...')
    try:
        with session.get(url, stream=True, timeout=(15, 90)) as response:
            response.raise_for_status()
            with pending.open('wb') as f:
                for chunk in response.iter_content(chunk_size=128 * 1024):
                    if chunk:
                        f.write(chunk)
        rows = validate(pending, split)
        if len(rows) != EXPECTED[split]:
            raise ValueError(
                f'{split}: so dong {len(rows)} khac {EXPECTED[split]} tren dataset card; '
                'can kiem tra phien ban nguon.'
            )
        pending.replace(final)
        print(f'  {split}: {len(rows)} dong, SHA256 {digest(final)[:16]}...')
        return final
    finally:
        pending.unlink(missing_ok=True)


def main() -> int:
    FOLDER.mkdir(parents=True, exist_ok=True)
    print('TIKILENS - TAI NGUON 2 QUA FILE JSON GOC')
    print('Khong su dung API /rows; KHONG truy cap MongoDB.')
    counts = {}
    source_counts = Counter()
    seen_ids = set()
    file_hashes = {}
    tmp = OUTPUT.with_name(OUTPUT.name + '.new')
    session = requests.Session()
    try:
        with tmp.open('w', encoding='utf-8', newline='\n') as out:
            for split in SPLITS:
                path = download(session, split)
                file_hashes[path.name] = digest(path)
                records = validate(path, split)
                counts[split] = len(records)
                for item in records:
                    item_id = str(item['id'])
                    if item_id in seen_ids:
                        raise ValueError('Trung ID giua cac splits: ' + item_id)
                    seen_ids.add(item_id)
                    doc = dict(item)
                    doc['_dataset_split'] = split
                    doc['_dataset_id'] = DATASET_ID
                    out.write(json.dumps(doc, ensure_ascii=False) + '\n')
                    source_counts[str(doc['source'])] += 1

        total = sum(counts.values())
        if total != 7066:
            raise ValueError(f'Tong {total} khac 7066, can kiem tra dataset card.')
        new_manifest = {
            'dataset_id': DATASET_ID,
            'dataset_url': BASE_URL,
            'download_method': 'Direct raw JSON files (/resolve/main/) without datasets-server rows API',
            'downloaded_at_utc': datetime.now(timezone.utc).isoformat(),
            'license_as_declared_by_publisher': 'CC-BY-SA-4.0',
            'attribution': 'Tamir39/causasent-ate-v2; original CausaSent project',
            'split_counts': counts,
            'source_counts': dict(source_counts),
            'total_rows': total,
            'source_file_sha256': file_hashes,
            'combined_file': OUTPUT.name,
            'combined_sha256': digest(tmp),
            'cautions': [
                'This is a published secondary dataset, NOT independently scraped Tiki data.',
                'Some reviews originate on Tiki and may overlap existing raw_reviews.',
                'Gold vs LLM-labelled silver quality differs; audit labels before modelling.',
                'Preserve train/val/test splits for leakage-free evaluations.',
                'Review CC BY-SA 4.0 attribution and redistribution obligations.',
            ],
        }
        pending_manifest = MANIFEST.with_name(MANIFEST.name + '.new')
        pending_manifest.write_text(
            json.dumps(new_manifest, ensure_ascii=False, indent=2) + '\n',
            encoding='utf-8',
        )
        tmp.replace(OUTPUT)
        pending_manifest.replace(MANIFEST)
        print('\nTAI NGUON 2 THANH CONG!')
        print('Train:', counts['train'])
        print('Val:', counts['val'])
        print('Test:', counts['test'])
        print('TONG:', total)
        print('Nguon goc:', dict(source_counts))
        print('File:', OUTPUT)
        print('Manifest:', MANIFEST)
        print('MongoDB: KHONG BI THAY DOI.')
        return 0
    except (requests.RequestException, OSError, ValueError) as exc:
        print('\nCHUA TAI HOAN TAT!')
        print('Loai loi:', type(exc).__name__)
        print('Chi tiet:', str(exc)[:350])
        print('MongoDB: KHONG BI THAY DOI.')
        return 1
    finally:
        tmp.unlink(missing_ok=True)
        session.close()


if __name__ == '__main__':
    sys.exit(main())
