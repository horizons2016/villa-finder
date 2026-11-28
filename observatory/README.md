# RAI Property Intelligence · راي للذكاء العقاري

Bilingual property directory and real estate observatory for Oman. The observatory lives on `ai/property-observatory`. Villa Finder and its Jaalan page continue on the existing production branch.

## Run locally

From the repository root:

```sh
cd observatory
python -m unittest discover -s tests -v
python -m rai legacy
python -m rai collect
python -m rai export state/public-data.json
python -m rai build dist --snapshot state/public-data.json
python -m http.server 8765 --bind 127.0.0.1 --directory dist
```

Open http://127.0.0.1:8765/. The repository's vetted snapshot can be used offline with `python -m rai build dist`. The map background and external source links require connectivity. Python 3.11+, SQLite 3.38+ and Poppler `pdftotext` are required for the full collection workflow.

The preview includes sourced official figures and a geospatial layer. The public listing view opens as an empty directory until there is an appropriately authorized listing source. The legacy inventory is preserved in the private operational database. See [project status](PROJECT_STATUS.md), [architecture](ARCHITECTURE.md), [data dictionary](DATA_DICTIONARY.md), [source registry](SOURCE_REGISTRY.md), [deployment](DEPLOYMENT.md), [test report](TEST_REPORT.md) and [changelog](CHANGELOG.md).

## البيانات المعروضة

تعرض المنصة الإحصاءات الرسمية مع رابط إصدارها. وتعرض الإعلانات المصرح بنشرها عند توفرها، مع حالة التحقق من الإعلان وسجل الرصد. تتوافر المحافظة والولاية في جميع أنحاء السلطنة، وتتبع تغطية الإعلانات والخدمات البيانات المتاحة لكل مصدر.
