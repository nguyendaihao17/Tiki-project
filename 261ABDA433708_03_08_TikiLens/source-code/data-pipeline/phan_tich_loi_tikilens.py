"""TIKILENS VN - read-only follow-up checks on reviews / sellers.
Run: py phan_tich_loi_tikilens.py
Needs: pymongo, python-dotenv, .env alongside this script.
Does NOT write, update, or delete any MongoDB documents.
"""
from collections import Counter
from pathlib import Path
from dotenv import dotenv_values
from pymongo import MongoClient

folder = Path(__file__).resolve().parent
uri = dotenv_values(folder / '.env').get('MONGO_URI')
if not uri:
    raise ValueError('Khong tim thay MONGO_URI trong .env cung thu muc.')

# Tinh gia tri rong theo cung quy tac nhu bao cao truoc.
EMPTY_MARKERS = {'', 'null', 'none', 'nan', 'n/a', '-'}

def key(value):
    return '' if value is None else str(value).strip()

def is_missing(value):
    return key(value).lower() in EMPTY_MARKERS

try:
    with MongoClient(uri, serverSelectionTimeoutMS=15000) as client:
        client.admin.command('ping')
        db = client['tikilens_vn']

        sellers = {
            key(item.get('seller_id'))
            for item in db.raw_sellers.find({}, {'seller_id': 1, '_id': 0})
            if not is_missing(item.get('seller_id'))
        }
        product_seller = {
            key(item.get('product_id')): key(item.get('seller_id'))
            for item in db.raw_products.find(
                {}, {'product_id': 1, 'seller_id': 1, '_id': 0}
            )
            if not is_missing(item.get('product_id'))
        }

        total = 0
        missing_content = 0
        has_title_when_content_missing = 0
        reviews_with_unknown_seller = 0
        distinct_unknown_sellers = set()
        unknown_seller_but_product_has_known_seller = 0
        reviews_seller_differs_from_product = 0
        unknown_products = 0
        ratings_all = Counter()
        ratings_missing_content = Counter()
        sentiments_all = Counter()
        sentiments_missing_content = Counter()

        for review in db.raw_reviews.find({}, {
            '_id': 0, 'product_id': 1, 'seller_id': 1,
            'content': 1, 'title': 1, 'rating': 1, 'sentiment': 1
        }).batch_size(500):
            total += 1
            sid = key(review.get('seller_id'))
            pid = key(review.get('product_id'))
            rating = key(review.get('rating')) or '(missing)'
            sentiment = key(review.get('sentiment')) or '(missing)'
            ratings_all[rating] += 1
            sentiments_all[sentiment] += 1

            if is_missing(review.get('content')):
                missing_content += 1
                ratings_missing_content[rating] += 1
                sentiments_missing_content[sentiment] += 1
                if not is_missing(review.get('title')):
                    has_title_when_content_missing += 1

            if sid not in sellers:
                reviews_with_unknown_seller += 1
                distinct_unknown_sellers.add(sid)
                if pid in product_seller and product_seller[pid] in sellers:
                    unknown_seller_but_product_has_known_seller += 1

            if pid not in product_seller:
                unknown_products += 1
            elif sid != product_seller[pid]:
                reviews_seller_differs_from_product += 1

        def formatted(counter):
            return ', '.join(f'{v}: {n}' for v, n in sorted(counter.items())) or '(none)'

        lines = [
            'TIKILENS VN - KIEM TRA SAU BAO CAO CHAT LUONG',
            'CHE DO: CHI DOC; KHONG SUA DU LIEU MONGODB',
            '',
            'I. SO LUONG & LIEN KET',
            f'Tong reviews: {total}',
            f'Sellers khac nhau trong raw_sellers: {len(sellers)}',
            f'Reviews co seller_id khong co trong raw_sellers: {reviews_with_unknown_seller}',
            f'So seller_id khong ton tai khac nhau: {len(distinct_unknown_sellers)}',
            'Reviews seller_id khong co trong raw_sellers nhung product co seller_id hop le: '
            f'{unknown_seller_but_product_has_known_seller}',
            f'Reviews seller_id khac seller_id hien tai cua product: {reviews_seller_differs_from_product}',
            f'Reviews co product_id khong co trong raw_products: {unknown_products}',
            '',
            'II. CHAT LUONG NOI DUNG REVIEW',
            f'Reviews thieu content: {missing_content}',
            f'Reviews thieu content nhung co title: {has_title_when_content_missing}',
            f'Reviews co content: {total - missing_content}',
            f'Ty le thieu content: {missing_content / total:.2%}' if total else 'Khong co reviews',
            '',
            'III. PHAN BO NHAN',
            f'Rating - tat ca: {formatted(ratings_all)}',
            f'Rating - thieu content: {formatted(ratings_missing_content)}',
            f'Sentiment - tat ca: {formatted(sentiments_all)}',
            f'Sentiment - thieu content: {formatted(sentiments_missing_content)}',
            '',
            'IV. KET LUAN THAO TAC',
            '- Khong tu dong gan seller_id moi cho reviews chua khop; co the la lich su giao dich.',
            '- Khong tu dong xoa reviews thieu content; review rating-only van co gia tri.',
            '- Truoc khi NLP, chi lay reviews co content hoac can nhac ket hop title.',
            '- Chua kiem chung do dung cua nhan sentiment va nguon du lieu.',
        ]
        result = folder / 'tikilens_diagnostics.txt'
        result.write_text('\n'.join(lines) + '\n', encoding='utf-8')
        print('KIEM TRA CHUYEN SAU THANH CONG!')
        print('Tong reviews:', total)
        print('Reviews thieu content:', missing_content)
        print('Reviews khong khop seller:', reviews_with_unknown_seller)
        print('Bao cao:', result)
        print('MongoDB: KHONG BI THAY DOI')
except Exception as exc:
    # Do not print full exception text: it may expose a connection string.
    print('LOI:', type(exc).__name__)
    raise SystemExit(1)
